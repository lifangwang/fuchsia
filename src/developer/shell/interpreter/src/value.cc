// Copyright 2020 The Fuchsia Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "src/developer/shell/interpreter/src/value.h"

#include <cstdint>
#include <string>

#include "src/developer/shell/interpreter/src/schema.h"

namespace shell {
namespace interpreter {

void Value::Set(const Value& value) {
  // For types which need to take a reference, we take the reference before we release the old
  // value. This way, we don't end with a reference to a destroyed value if the user assigns a
  // value to itself.
  switch (value.type_) {
    case ValueType::kUndef:
      Release();
      break;
    case ValueType::kInt8:
      Release();
      int8_value_ = value.int8_value_;
      break;
    case ValueType::kUint8:
      Release();
      uint8_value_ = value.uint8_value_;
      break;
    case ValueType::kInt16:
      Release();
      int16_value_ = value.int16_value_;
      break;
    case ValueType::kUint16:
      Release();
      uint16_value_ = value.uint16_value_;
      break;
    case ValueType::kInt32:
      Release();
      int32_value_ = value.int32_value_;
      break;
    case ValueType::kUint32:
      Release();
      uint32_value_ = value.uint32_value_;
      break;
    case ValueType::kInt64:
      Release();
      int64_value_ = value.int64_value_;
      break;
    case ValueType::kUint64:
      Release();
      uint64_value_ = value.uint64_value_;
      break;
    case ValueType::kString: {
      String* string = value.string_->Use();
      Release();
      string_ = string;
      break;
    }
    case ValueType::kObject: {
      Object* object = value.object_->Use();
      Release();
      object_ = object;
      break;
    }
  }
  type_ = value.type_;
}

void Value::Release() {
  switch (type_) {
    case ValueType::kUndef:
    case ValueType::kInt8:
    case ValueType::kUint8:
    case ValueType::kInt16:
    case ValueType::kUint16:
    case ValueType::kInt32:
    case ValueType::kUint32:
    case ValueType::kInt64:
    case ValueType::kUint64:
      break;
    case ValueType::kString:
      string_->Release();
      break;
    case ValueType::kObject:
      object_->Release();
      break;
  }
}

const std::shared_ptr<ObjectSchema> Object::schema() { return schema_; }

std::unique_ptr<Value> Object::GetField(ObjectFieldSchema* field) const {
  FX_DCHECK(field != nullptr) << "Invalid field pointer passed to getfield";
  uint64_t offset = field->offset();
  std::unique_ptr<Value> v = std::make_unique<Value>();
  const uint8_t* ptr = reinterpret_cast<const uint8_t*>(this) + offset;
  // TODO: We need to factorize this code with Type::LoadVariable.  This probably involves
  // merging ValueKind and TypeKind.
  switch (field->type()->Kind()) {
    case Type::TypeKind::kInt8:
      v->SetInt8(*reinterpret_cast<const int8_t*>(ptr));
      break;
    case Type::TypeKind::kUint8:
      v->SetUint8(*reinterpret_cast<const uint8_t*>(ptr));
      break;
    case Type::TypeKind::kInt16:
      v->SetInt16(*reinterpret_cast<const int16_t*>(ptr));
      break;
    case Type::TypeKind::kUint16:
      v->SetUint16(*reinterpret_cast<const uint16_t*>(ptr));
      break;
    case Type::TypeKind::kInt32:
      v->SetInt32(*reinterpret_cast<const int32_t*>(ptr));
      break;
    case Type::TypeKind::kUint32:
      v->SetUint32(*reinterpret_cast<const uint32_t*>(ptr));
      break;
    case Type::TypeKind::kInt64:
      v->SetInt64(*reinterpret_cast<const int64_t*>(ptr));
      break;
    case Type::TypeKind::kUint64:
      v->SetUint64(*reinterpret_cast<const uint64_t*>(ptr));
      break;
    case Type::TypeKind::kString:
      v->SetString(const_cast<String*>(reinterpret_cast<const String*>(ptr)));
      break;
    case Type::TypeKind::kObject:
      v->SetObject(const_cast<Object*>(reinterpret_cast<const Object*>(ptr)));
      break;
    default:
      FX_NOTREACHED() << "Unknown type in getfield";
      // Assert unknown type.
      break;
  }
  return v;
}

void Object::SetField(ObjectFieldSchema* field, uint64_t value) {
  const Type* field_type = field->type();
  const void* dest = reinterpret_cast<const uint8_t*>(this) + field->offset();
  FX_DCHECK(field_type->Size() <= sizeof(uint64_t))
      << "Big value in stack.  "
         "Can't assign that to object field yet.  File a bug.";
  memcpy(const_cast<void*>(dest), &value, field_type->Size());
}

void Object::Free() { schema()->AsObjectSchema()->FreeObject(this); }

}  // namespace interpreter
}  // namespace shell
