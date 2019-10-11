// Copyright 2018 The Fuchsia Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef SRC_CONNECTIVITY_WLAN_LIB_MLME_CPP_INCLUDE_WLAN_MLME_RUST_UTILS_H_
#define SRC_CONNECTIVITY_WLAN_LIB_MLME_CPP_INCLUDE_WLAN_MLME_RUST_UTILS_H_

#include <memory>

#include <src/connectivity/wlan/lib/mlme/rust/c-binding/bindings.h>
#include <wlan/common/macaddr.h>

namespace wlan {

using SequenceManager =
    std::unique_ptr<mlme_sequence_manager_t, void (*)(mlme_sequence_manager_t*)>;
using ClientStation = std::unique_ptr<wlan_client_sta_t, void (*)(wlan_client_sta_t*)>;
using ApStation = std::unique_ptr<wlan_ap_sta_t, void (*)(wlan_ap_sta_t*)>;

SequenceManager NewSequenceManager();
ClientStation NewClientStation(mlme_device_ops_t device, mlme_buffer_provider_ops_t buf_provider,
                               wlan_scheduler_ops_t scheduler, common::MacAddr bssid,
                               common::MacAddr iface_mac);
ApStation NewApStation(mlme_device_ops_t device, mlme_buffer_provider_ops_t buf_provider,
                       common::MacAddr bssid);

}  // namespace wlan

#endif  // SRC_CONNECTIVITY_WLAN_LIB_MLME_CPP_INCLUDE_WLAN_MLME_RUST_UTILS_H_
