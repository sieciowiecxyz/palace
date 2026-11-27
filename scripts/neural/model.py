# SPDX-License-Identifier: Apache-2.0
"""Orientation-equivariant operator network and fixed complex sparse multiply."""

import torch
from torch import nn

BLOCKS, WIDTH, K, PHI, FEATURES, CONTEXT = 6, 16, 8, 8, 7, 3
REAL = torch.float64
COMPLEX = torch.complex128


def fixed_csr(indptr, indices, values, n):
    real, imag = (
        torch.sparse_csr_tensor(indptr, indices, part.contiguous(), size=(n, n))
        for part in (values.real, values.imag)
    )

    def apply(x):
        xr, xi = x.real.contiguous(), x.imag.contiguous()
        return torch.complex(
            torch.sparse.mm(real, xr) - torch.sparse.mm(imag, xi),
            torch.sparse.mm(real, xi) + torch.sparse.mm(imag, xr),
        )

    return apply


class ComplexMap(nn.Module):
    def __init__(self, inputs, outputs):
        super().__init__()
        self.real = nn.Parameter(torch.empty(inputs, outputs, dtype=REAL))
        self.imag = nn.Parameter(torch.empty(inputs, outputs, dtype=REAL))
        for part in (self.real, self.imag):
            nn.init.normal_(part, std=(2 * inputs) ** -0.5)

    def forward(self, x):
        return x @ torch.complex(self.real, self.imag)


class Gate(nn.Module):
    def __init__(self):
        super().__init__()
        self.weight = nn.Parameter(torch.zeros(WIDTH + FEATURES + CONTEXT, WIDTH, dtype=REAL))
        self.bias = nn.Parameter(torch.zeros(WIDTH, dtype=REAL))

    def forward(self, x):
        return torch.sigmoid(x @ self.weight + self.bias)


class OperatorBlock(nn.Module):
    def __init__(self):
        super().__init__()
        self.local = ComplexMap(WIDTH, WIDTH)
        self.operator = ComplexMap(WIDTH, WIDTH)
        self.gate = Gate()

    def forward(self, h, sparse, invariant, free):
        gate = self.gate(torch.cat((h.abs(), invariant), dim=1))
        return free * (h + gate * (self.local(h) + self.operator(sparse(h))))


class OperatorNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.lift = ComplexMap(PHI, WIDTH)
        self.blocks = nn.ModuleList(OperatorBlock() for _ in range(BLOCKS))
        self.readout = ComplexMap(WIDTH, K)

    def forward(self, phi, sparse_normalized, features, context, free):
        invariant = torch.cat((features, context.expand(phi.shape[0], -1)), dim=1)
        free = free[:, None]
        h = self.lift(phi)
        for block in self.blocks:
            h = block(h, sparse_normalized, invariant, free)
        return free * self.readout(h)
