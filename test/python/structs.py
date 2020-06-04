#a Copyright
#  
#  This file 'test_8b10b.py' copyright Gavin J Stark 2020
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#a Signal types
#t t_tbi_valid
t_tbi_valid = {"valid":1, "data":10}

#t t_gmii_tx
t_gmii_tx = {"tx_en":1, "tx_er":1, "txd":8}

#t t_gmii_rx
t_gmii_rx = {"rx_dv":1, "rx_er":1, "rxd":8, "rx_crs":1}

#t t_sgmii_gasket_trace
t_sgmii_gasket_trace = {
    "valid":1,
    "an_fsm":3,
    "rx_config_data_match":6,
    "debug_count":8,
    "comma_found":10,
    "rx_fsm":4,
    "seeking_comma":1,
    "rx_sync":1,
    "symbol_valid":1,
    "symbol_is_control":1,
    "symbol_is_K":1,
    "symbol_is_S":1,
    "symbol_is_V":1,
    "symbol_is_T":1,
    "symbol_is_R":1,
    "symbol_data":8,
    }

#t t_sgmii_gasket_control
t_sgmii_gasket_control = {"write_config":1, "write_address":4, "write_data":32}

#t t_sgmii_gasket_status
t_sgmii_gasket_status = {"rx_sync":1, "rx_sync_toggle":1, "rx_symbols_since_sync":32, "an_config":16, "trace":t_sgmii_gasket_trace}

#t t_dec_8b10b_data - t_8b10b_dec_data
t_dec_8b10b_data = {
    "valid":1,
    "data":8,
    "is_control":1,
    "is_data":1,
    "disparity_positive":1,
}

#t t_symbol_8b10b - t_8b10b_symbol
t_symbol_8b10b = {
    "disparity_positive":1,
    "symbol":10,
}

#t t_enc_8b10b_data -  t_8b10b_enc_data
t_enc_8b10b_data = {
    "data":8,
    "is_control":1,
    "disparity":1,
}

