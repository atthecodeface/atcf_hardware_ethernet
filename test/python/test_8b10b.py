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

#a Documentation
"""
"""

#a Imports
from cdl.sim     import ThExecFile
from cdl.sim     import HardwareThDut
from cdl.sim     import TestCase
from cdl.utils   import csr
from .encdec_8b10b import find_encoding, encodings_8b10b

#a Signal types
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

#a Test classes
#c Code8b10bTest_Base
class Code8b10bTest_Base(ThExecFile):
    """
    """
    #f run__init - invoked by submodules
    def run__init(self):
        self.bfm_wait(10)
        pass

    #f run
    def run(self):
        pass

    #f run__finalize
    def run__finalize(self):
        self.passtest("Test completed")
        pass

#c Code8b10bTest_Encode_0
class Code8b10bTest_Encode_0(Code8b10bTest_Base):
    """
    """
    #f run
    def run(self):
        for e in encodings_8b10b:
            self.enc_data__data.drive(e.data)
            self.enc_data__is_control.drive(e.is_control)
            self.enc_data__disparity.drive(e.disparity_in)
            self.bfm_wait(2)
            dut_disparity_out = self.enc_symbol__disparity_positive.value()
            dut_encoding      = self.enc_symbol__symbol.value()
            self.compare_expected("Encoding of symbol %s"%(str(e)),e.encoding,dut_encoding)
            self.compare_expected("Disparity out of symbol %s"%(str(e)),e.disparity_out,dut_disparity_out)
            pass
        pass

#c Code8b10bTest_Decode_0
class Code8b10bTest_Decode_0(Code8b10bTest_Base):
    """
    """
    #f run
    def run(self):
        for e in encodings_8b10b:
            self.enc_data__data.drive(e.data)
            self.enc_data__is_control.drive(e.is_control)
            self.enc_data__disparity.drive(e.disparity_in)
            self.bfm_wait(2)
            dut_disparity_out = self.enc_symbol__disparity_positive.value()
            dut_encoding      = self.enc_symbol__symbol.value()
            self.dec_symbol__disparity_positive.drive(e.disparity_in)
            self.dec_symbol__symbol.drive(dut_encoding)
            self.bfm_wait(2)
            dut_valid = self.dec_data__valid.value()
            dut_data = self.dec_data__data.value()
            dut_is_control = self.dec_data__is_control.value()
            dut_is_data = self.dec_data__is_data.value()
            dut_disparity_out = self.dec_data__disparity_positive.value()
            self.compare_expected("Decoding of symbol %s valid"%(str(e)),1,dut_valid)
            self.compare_expected("Data of symbol %s"%(str(e)),e.data,dut_data)
            self.compare_expected("Is control of symbol %s"%(str(e)),e.is_control,dut_is_control)
            self.compare_expected("Is data of symbol %s"%(str(e)),1^e.is_control,dut_is_data)
            self.compare_expected("Disparity out of symbol %s"%(str(e)),e.disparity_out,dut_disparity_out)
            pass
        self.bfm_wait(10)
        self.enc_data__data.drive(0)
        pass

#c Code8b10bTest_Decode_1
class Code8b10bTest_Decode_1(Code8b10bTest_Base):
    """
    """
    #f run
    def run(self):
        pass
        for symbol in range(1024):
            for disp in range(2):
                e = find_encoding(encodings_8b10b, {"encoding":symbol, "disparity_in":disp})
                self.dec_symbol__disparity_positive.drive(disp)
                self.dec_symbol__symbol.drive(symbol)
                self.bfm_wait(2)
                dut_valid = self.dec_data__valid.value()
                dut_data = self.dec_data__data.value()
                dut_is_control = self.dec_data__is_control.value()
                dut_is_data = self.dec_data__is_data.value()
                dut_disparity_out = self.dec_data__disparity_positive.value()
                if e is None:
                    self.compare_expected("Decoding of code %03d should be invalid"%(symbol),0,dut_valid)
                    pass
                else:
                    self.compare_expected("Decoding of code %s valid"%(str(e)),1,dut_valid)
                    self.compare_expected("Data of symbol %s"%(str(e)),e.data,dut_data)
                    self.compare_expected("Is control of symbol %s"%(str(e)),e.is_control,dut_is_control)
                    self.compare_expected("Is data of symbol %s"%(str(e)),1^e.is_control,dut_is_data)
                    self.compare_expected("Disparity out of symbol %s"%(str(e)),e.disparity_out,dut_disparity_out)
                    pass
                pass
            pass
        self.bfm_wait(10)
        self.enc_data__data.drive(0)
        pass
    pass

#a Hardware classes
#c Code8b10bHw
class Code8b10bHw(HardwareThDut):
    clock_desc = [("clk",(0,1,1)),
    ]
    reset_desc = {"name":"reset_n", "init_value":0, "wait":5}
    module_name = "tb_8b10b"
    dut_inputs  = {"dec_symbol":t_symbol_8b10b,
                   "enc_data":t_enc_8b10b_data,
    }
    dut_outputs = {"enc_symbol":t_symbol_8b10b,
                   "dec_data":t_dec_8b10b_data,
    }
    pass

#a Simulation test classes
#c Code8b10b
class Code8b10b(TestCase):
    hw = Code8b10bHw
    kwargs = {
     # "verbosity":0,
        }
    _tests = {
        "enc_0"  : (Code8b10bTest_Encode_0, 5*1000,  kwargs),
        "dec_0"  : (Code8b10bTest_Decode_0, 8*1000,  kwargs),
        "dec_1"  : (Code8b10bTest_Decode_1,10*1000,  kwargs),
        "smoke"  : (Code8b10bTest_Decode_0, 8*1000,  kwargs),
    }
    pass

