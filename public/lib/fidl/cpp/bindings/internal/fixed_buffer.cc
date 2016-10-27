// Copyright 2014 The Fuchsia Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "lib/fidl/cpp/bindings/internal/fixed_buffer.h"

#include <stdlib.h>

#include <algorithm>

#include "lib/fidl/cpp/bindings/internal/bindings_serialization.h"
#include "lib/ftl/logging.h"

namespace fidl {
namespace internal {

FixedBuffer::FixedBuffer() : ptr_(nullptr), cursor_(0), size_(0) {}

void FixedBuffer::Initialize(void* memory, size_t size) {
  ptr_ = static_cast<char*>(memory);
  cursor_ = 0;
  size_ = size;
}

void* FixedBuffer::Allocate(size_t delta) {
  // Ensure that all memory returned by Allocate() is 8-byte aligned w.r.t the
  // start of the buffer.
  delta = internal::Align(delta);

  if (delta == 0 || delta > size_ - cursor_) {
    FTL_DCHECK(false) << "Not reached";
    return nullptr;
  }

  char* result = ptr_ + cursor_;
  cursor_ += delta;

  return result;
}

FixedBufferForTesting::FixedBufferForTesting(size_t size) {
  size_ = internal::Align(size);
  // Use calloc here to ensure all message memory is zero'd out.
  ptr_ = static_cast<char*>(calloc(size_, 1));
}

FixedBufferForTesting::~FixedBufferForTesting() {
  free(ptr_);
}

void* FixedBufferForTesting::Leak() {
  char* ptr = ptr_;
  ptr_ = nullptr;
  cursor_ = 0;
  size_ = 0;
  return ptr;
}

}  // namespace internal
}  // namespace fidl
