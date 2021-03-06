// Copyright 2019 The Fuchsia Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include <lib/virtio/driver_utils.h>
#include <zircon/types.h>

#include <ddk/driver.h>

#include "ethernet.h"
#include "src/connectivity/ethernet/drivers/virtio/virtio_ethernet-bind.h"

static const zx_driver_ops_t virtio_ethernet_driver_ops = []() {
  zx_driver_ops_t ops = {};
  ops.version = DRIVER_OPS_VERSION;
  ops.bind = CreateAndBind<virtio::EthernetDevice>;
  return ops;
}();

ZIRCON_DRIVER(virtio_ethernet, virtio_ethernet_driver_ops, "zircon", "0.1")
