// Experimental complex FP64 H-matrix apply. No change to Palace or discretization.
#include <cuda_runtime.h>
#include <cstddef>
#include <memory>
#include <new>
#include <vector>

struct HostBlock
{
  int i, j, m, n, rank;
  const double2 *left, *right; // Column-major host arrays, retained by caller during create.
};
static_assert(sizeof(HostBlock) == 40, "Python ctypes ABI mismatch");

struct Block
{
  size_t value_offset;
  int rows, columns, input_offset, output_offset, temporary;
};
struct Row { int block, row; };

__global__ void ApplyRows(const Block *blocks, const Row *tasks, int count,
                          const double2 *values, const double2 *x,
                          double2 *y, double2 *temporary)
{
  const int work = (blockIdx.x * blockDim.x + threadIdx.x) / 32;
  const int lane = threadIdx.x % 32;
  if (work >= count) { return; } // Every lane of a warp takes the same branch.
  const Row task = tasks[work];
  const Block b = blocks[task.block];
  const double2 *a = values + b.value_offset + size_t(task.row) * b.columns;
  double real = 0., imag = 0.;
  for (int col = lane; col < b.columns; col += 32)
  {
    const double2 v = a[col], w = x[b.input_offset + col];
    real += v.x * w.x - v.y * w.y;
    imag += v.x * w.y + v.y * w.x;
  }
  for (int offset = 16; offset; offset /= 2)
  {
    real += __shfl_down_sync(0xffffffff, real, offset);
    imag += __shfl_down_sync(0xffffffff, imag, offset);
  }
  if (!lane)
  {
    if (b.temporary)
    {
      temporary[b.output_offset + task.row] = make_double2(real, imag);
    }
    else
    {
      atomicAdd(&y[b.output_offset + task.row].x, real);
      atomicAdd(&y[b.output_offset + task.row].y, imag);
    }
  }
}

struct Plan
{
  double2 *values = nullptr, *x = nullptr, *y = nullptr, *temporary = nullptr;
  Block *first = nullptr, *second = nullptr;
  Row *first_rows = nullptr, *second_rows = nullptr;
  int n = 0, first_count = 0, second_count = 0;
  size_t bytes = 0;
  ~Plan()
  {
    cudaFree(values); cudaFree(x); cudaFree(y); cudaFree(temporary);
    cudaFree(first); cudaFree(second); cudaFree(first_rows); cudaFree(second_rows);
  }
  template <class T> cudaError_t Allocate(T *&p, size_t count)
  {
    if (!count) { return cudaSuccess; }
    auto status = cudaMalloc(reinterpret_cast<void **>(&p), count * sizeof(T));
    if (status == cudaSuccess) { bytes += count * sizeof(T); }
    return status;
  }
  template <class T> cudaError_t Upload(T *&p, const std::vector<T> &data)
  {
    auto status = Allocate(p, data.size());
    if (status != cudaSuccess || data.empty()) { return status; }
    return cudaMemcpy(p, data.data(), data.size() * sizeof(T), cudaMemcpyHostToDevice);
  }
};

extern "C" size_t hm_block_size() { return sizeof(HostBlock); }

extern "C" int hm_create(const HostBlock *input, int count, int n,
                          void **output, size_t *bytes)
{
  if (!input || !output || !bytes || count <= 0 || n <= 0) { return cudaErrorInvalidValue; }
  *output = nullptr;
  try
  {
    auto plan = std::make_unique<Plan>();
    plan->n = n;
    std::vector<double2> values;
    std::vector<Block> first, second;
    std::vector<Row> first_rows, second_rows;
    int temporary_size = 0;
    auto append = [&](const double2 *data, int m, int cols, int in, int out, bool temp,
                      std::vector<Block> &blocks, std::vector<Row> &tasks)
    {
      const int index = int(blocks.size());
      blocks.push_back({values.size(), m, cols, in, out, int(temp)});
      // Transpose storage, not the operator: contiguous columns within each dot product.
      for (int row = 0; row < m; row++)
      {
        for (int col = 0; col < cols; col++) { values.push_back(data[row + size_t(col) * m]); }
        tasks.push_back({index, row});
      }
    };
    for (int k = 0; k < count; k++)
    {
      const auto &b = input[k];
      if (b.i < 0 || b.j < 0 || b.m <= 0 || b.n <= 0 || b.i > n - b.m ||
          b.j > n - b.n || b.rank < 0 || b.rank > b.m || b.rank > b.n ||
          !b.left || (b.rank && !b.right)) { return cudaErrorInvalidValue; }
      if (b.rank)
      {
        append(b.right, b.rank, b.n, b.j, temporary_size, true, first, first_rows);
        append(b.left, b.m, b.rank, temporary_size, b.i, false, second, second_rows);
        temporary_size += b.rank;
      }
      else { append(b.left, b.m, b.n, b.j, b.i, false, first, first_rows); }
    }
    plan->first_count = int(first_rows.size());
    plan->second_count = int(second_rows.size());
    cudaError_t status;
#define TRY(call) do { status = (call); if (status != cudaSuccess) { return status; } } while (false)
    TRY(plan->Upload(plan->values, values));
    TRY(plan->Upload(plan->first, first)); TRY(plan->Upload(plan->second, second));
    TRY(plan->Upload(plan->first_rows, first_rows)); TRY(plan->Upload(plan->second_rows, second_rows));
    TRY(plan->Allocate(plan->x, n)); TRY(plan->Allocate(plan->y, n));
    TRY(plan->Allocate(plan->temporary, temporary_size));
    *bytes = plan->bytes;
    *output = plan.release();
    return cudaSuccess;
  }
  catch (const std::bad_alloc &) { return cudaErrorMemoryAllocation; }
}

extern "C" int hm_apply(void *opaque, const double2 *x, double2 *y, int repeat,
                         float *average_kernel_ms)
{
  auto *plan = static_cast<Plan *>(opaque);
  if (!plan || !x || !y || !average_kernel_ms || repeat <= 0 || repeat > 1024)
  { return cudaErrorInvalidValue; }
  cudaError_t status;
  TRY(cudaMemcpy(plan->x, x, plan->n * sizeof(double2), cudaMemcpyHostToDevice));
  cudaEvent_t start, end;
  TRY(cudaEventCreate(&start));
  status = cudaEventCreate(&end);
  if (status != cudaSuccess) { cudaEventDestroy(start); return status; }
  auto execute = [&]() -> cudaError_t
  {
    TRY(cudaEventRecord(start));
    for (int r = 0; r < repeat; r++)
    {
      TRY(cudaMemsetAsync(plan->y, 0, plan->n * sizeof(double2)));
      ApplyRows<<<(plan->first_count + 7) / 8, 256>>>(plan->first, plan->first_rows,
        plan->first_count, plan->values, plan->x, plan->y, plan->temporary);
      TRY(cudaGetLastError());
      if (plan->second_count)
      {
        ApplyRows<<<(plan->second_count + 7) / 8, 256>>>(plan->second, plan->second_rows,
          plan->second_count, plan->values, plan->temporary, plan->y, plan->temporary);
        TRY(cudaGetLastError());
      }
    }
    TRY(cudaEventRecord(end)); TRY(cudaEventSynchronize(end));
    TRY(cudaEventElapsedTime(average_kernel_ms, start, end));
    *average_kernel_ms /= repeat;
    TRY(cudaMemcpy(y, plan->y, plan->n * sizeof(double2), cudaMemcpyDeviceToHost));
    return cudaSuccess;
  };
  status = execute();
  cudaEventDestroy(start); cudaEventDestroy(end);
  return status;
#undef TRY
}

extern "C" void hm_destroy(void *opaque) { delete static_cast<Plan *>(opaque); }
