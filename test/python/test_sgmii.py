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
from cdl.sim     import ThExecFile, LogEventParser
from cdl.sim     import HardwareThDut
from cdl.sim     import TestCase
from cdl.utils   import csr
from .encdec_8b10b import find_encoding, encodings_8b10b
from .structs    import t_tbi_valid, t_gmii_tx, t_gmii_rx, t_sgmii_gasket_control, t_sgmii_gasket_status
from typing import Optional, List

#a Test classes
#c TxGmiiLogParser - log event parser for tx gmii
class TxGmiiLogParser(LogEventParser):
    def filter_module(self, module_name:str) -> bool : return True
    def map_log_type(self, log_type:str) -> Optional[str] :
        if log_type in self.attr_map: return log_type
        return None
    attr_map = {"GMII_tx":{"is_control":1,"data":2,"disparity":3,"even":4}}
    pass

#c RxGmiiLogParser - log event parser for Rx gmii
class RxGmiiLogParser(LogEventParser):
    def filter_module(self, module_name:str) -> bool : return True
    def map_log_type(self, log_type:str) -> Optional[str] :
        if log_type in self.attr_map: return log_type
        return None
    attr_map = {"GMII_rx":{"dv":1,"er":2,"data":3}}
    pass

#c Tbi expectation classes
class TbiExp(object):
    def __init__(self, data, is_symbol=False, optional=False, even=None):
        self.data = data
        self.is_symbol = is_symbol
        self.optional = optional
        self.even = even
        self.encoding_p = find_encoding(encodings_8b10b,{"data":data,"is_control":is_symbol,"disparity_in":0})
        self.encoding_n = find_encoding(encodings_8b10b,{"data":data,"is_control":is_symbol,"disparity_in":1})
        pass
    def check_with_log(self, l) -> [bool, bool]:
        err=False
        if (self.even is not None) and l.even!=self.even: err=True
        if self.is_symbol != l.is_control: err=True
        if self.data != l.data: err=True
        return (err, self.optional)
    def __str__(self):
        if self.is_symbol:
            r="S%02x"%self.data
            pass
        else:
            r="D%02x"%self.data
            pass
        r += ":%d"%(int(self.optional))
        if self.even is not None: r+=":%d"%(int(self.even))
        return r
    pass
class TbiCtl(TbiExp):
    def __init__(self, **kwargs):
        super(TbiCtl,self).__init__(data=self.symbol, is_symbol=True, **kwargs)
        pass
    pass
class TbiD(TbiExp):
    def __init__(self, data, **kwargs):
        super(TbiD,self).__init__(data=data, **kwargs)
        pass
    pass
class TbiK(TbiCtl): symbol=0xbc
class TbiS(TbiCtl): symbol=0xfb    
class TbiT(TbiCtl): symbol=0xfd
class TbiR(TbiCtl): symbol=0xf7
class TbiV(TbiCtl): symbol=0xfe
class TbiExpPacket(object):
    expected_data : List[TbiExp]

#c SgmiiTest_Base
class SgmiiTest_Base(ThExecFile):
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

    #f gmii_bfm_wait
    def gmii_bfm_wait(self, delay):
        for i in range(delay):
            self.bfm_wait(1)
            while self.gmii_tx_enable.value()==0:
                self.bfm_wait(1)
                pass
            pass
        pass
    #f gmii_tx_check_expected_data
    def gmii_tx_check_expected_data(self):
        while (self.log_data.num_events()!=0) and (self.expected_symbols!=[]):
            l = self.log_data_parser.parse_log_event(self.log_data.event_pop())
            if l is None: continue
            while True:
                if self.expected_symbols==[]: raise Exception("expected_symbols was empty - can only occur if an optional symbol is at the end of the list, which is a bug")
                sym = self.expected_symbols.pop(0)
                (err,opt) = sym.check_with_log(l)
                if (not err) or (not opt): break
                pass
            if err:
                self.failtest("Symbol mismatch in tx data check (log %s symbol %s)"%(str(l),str(sym)))
                pass
            pass
        pass
    #f gmii_tx_pkt
    def gmii_tx_pkt(self, data, error_data=0, carrier_extend=0, ipg=8):
        self.expected_symbols.append(TbiS())
        dn = 0
        for d in data:
            if dn>0: self.expected_symbols.append(TbiD(d,optional=(dn==1)))
            dn = dn + 1
            self.gmii_tx__tx_en.drive(1)
            self.gmii_tx__tx_er.drive(0)
            self.gmii_tx__txd.drive(d)
            self.gmii_tx_enable.wait_for_value(1)
            self.bfm_wait(1)
            pass
        for i in range(error_data):
            self.gmii_tx__tx_en.drive(1)
            self.gmii_tx__tx_er.drive(1)
            self.gmii_tx_enable.wait_for_value(1)
            self.bfm_wait(1)
            pass
        self.expected_symbols.append(TbiT())
        for i in range(carrier_extend):
            self.expected_symbols.append(TbiR())
            self.gmii_tx__tx_en.drive(0)
            self.gmii_tx__tx_er.drive(1)
            self.gmii_tx_enable.wait_for_value(1)
            self.bfm_wait(1)
            pass
        self.expected_symbols.append(TbiR(even=True, optional=True))
        self.expected_symbols.append(TbiR(even=False))
        # We don't log the I after a packet
        # self.expected_symbols.append(TbiK(even=True, optional=True))
        for i in range(ipg):
            self.gmii_tx__tx_en.drive(0)
            self.gmii_tx__tx_er.drive(0)
            self.gmii_tx_enable.wait_for_value(1)
            self.bfm_wait(1)
            pass
        pass
    #f send_packet
    def send_packet(self, pkt):
        self.gmii_tx__tx_en.drive(1)
        self.gmii_tx__tx_er.drive(0)
        self.gmii_tx__txd.drive(0x55)
        self.gmii_bfm_wait(7)
        self.gmii_tx__txd.drive(0xd5)
        self.gmii_bfm_wait(1)
        for p in pkt:
            self.gmii_tx__txd.drive(p)
            self.gmii_bfm_wait(1)
            pass
        self.gmii_tx__tx_en.drive(0)
        self.gmii_tx__tx_er.drive(0)
        pass
    pass
    #f write_sgmii_control
    def write_sgmii_control(self, address, data):
        self.sgmii_gasket_control__write_config.drive(1)
        self.sgmii_gasket_control__write_address.drive(address)
        self.sgmii_gasket_control__write_data.drive(data)
        self.bfm_wait(1)
        self.sgmii_gasket_control__write_config.drive(0)
        self.bfm_wait(10)
        pass
    pass

#c SgmiiTest_0
class SgmiiTest_0(SgmiiTest_Base):
    #f run
    def run(self):
        self.bfm_wait(100)
        self.write_sgmii_control(0,100)
        self.write_sgmii_control(2,1)
        self.write_sgmii_control(1,32)

        self.bfm_wait(100)

        """
        Start of packet length 18 ptr 254
        01 00 00 00 ff ff ff ff ff ff 44 a8 42 29 88 ef 08 06 00 01 08 00 06 04 00 01 44 a8 42 29 88 ef 01 01 01 01 00 00 00 00 00 00 01 01 01 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 3f f7 82 00 00 00 00
        """
        pkt = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
               0x44, 0xa8, 0x42, 0x29, 0x88, 0xef,
               0x08, 0x06,
               0x00, 0x01, 0x08, 0x00, 0x06, 0x04, 0x00, 0x01,     0x44, 0xa8, 0x42, 0x29, 0x88, 0xef, 0x01, 0x01,
               0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,     0x01, 0x01, 0x01, 0x02, 0x00, 0x00, 0x00, 0x00,
               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
               ] # 02 3f f7 82

        self.bfm_wait(1000)
        for i in range(10):
            self.send_packet(pkt)
            self.gmii_bfm_wait(i+1)
            pass
        for i in range(10,1,-1):
            self.send_packet([0,1,2,3,4,5,6,7])
            self.gmii_bfm_wait(i+1)
            pass
        for i in range(5):
            self.send_packet([0,1,2,3,4,5,6,7])
            self.gmii_bfm_wait(1)
            pass
        self.gmii_bfm_wait(30)
                      
        pass


#c SgmiiTest_GmiiTx_Base
class SgmiiTest_GmiiTx_Base(SgmiiTest_Base):
    sgmii_module = "dut.sgg"
    #f run__init - invoked by submodules
    def run__init(self):
        self.bfm_wait(10)
        self.expected_symbols = []
        self.log_data         = self.log_recorder(self.sgmii_module)
        self.log_data_parser  = TxGmiiLogParser()
        self.write_sgmii_control(0,7)
        self.write_sgmii_control(0,3)
        # Wait and clear log queue - as the config/autonegotiation data will be in the log
        self.bfm_wait(100)
        self.gmii_tx_enable.wait_for_value(1)
        self.bfm_wait(1)
        while self.log_data.num_events()!=0:
            self.log_data.event_pop()
            pass
        pass

    #f gmii_tx_check_expected_data
    def gmii_tx_check_expected_data(self):
        while (self.log_data.num_events()!=0) and (self.expected_symbols!=[]):
            l = self.log_data_parser.parse_log_event(self.log_data.event_pop())
            if l is None: continue
            while True:
                if self.expected_symbols==[]: raise Exception("expected_symbols was empty - can only occur if an optional symbol is at the end of the list, which is a bug")
                sym = self.expected_symbols.pop(0)
                (err,opt) = sym.check_with_log(l)
                if (not err) or (not opt): break
                pass
            if err:
                self.failtest("Symbol mismatch in tx data check (log %s symbol %s)"%(str(l),str(sym)))
                pass
            pass
        pass
    #f gmii_tx_pkt
    def gmii_tx_pkt(self, data, error_data=0, carrier_extend=0, ipg=8):
        self.expected_symbols.append(TbiS())
        dn = 0
        for d in data:
            if dn>0: self.expected_symbols.append(TbiD(d,optional=(dn==1)))
            dn = dn + 1
            self.gmii_tx_enable.wait_for_value(1)
            self.gmii_tx__tx_en.drive(1)
            self.gmii_tx__tx_er.drive(0)
            self.gmii_tx__txd.drive(d)
            self.bfm_wait(1)
            pass
        for i in range(error_data):
            self.expected_symbols.append(TbiV())
            self.gmii_tx_enable.wait_for_value(1)
            self.gmii_tx__tx_en.drive(1)
            self.gmii_tx__tx_er.drive(1)
            self.bfm_wait(1)
            pass
        self.expected_symbols.append(TbiT())
        if carrier_extend==0:
            self.expected_symbols.append(TbiR(even=True, optional=True))
            self.expected_symbols.append(TbiR(even=False))
            pass
        else:
            cn = 0
            for i in range(carrier_extend):
                # one cycle provides T, one for the R at the end
                if (cn>=1): self.expected_symbols.append(TbiR())
                cn = cn + 1
                self.gmii_tx_enable.wait_for_value(1)
                self.gmii_tx__txd.drive(0xf)
                self.gmii_tx__tx_en.drive(0)
                self.gmii_tx__tx_er.drive(1)
                self.bfm_wait(1)
                pass
            self.expected_symbols.append(TbiR(even=True, optional=True))
            if ipg>0: # if ipg is 0 then we have added enough cycles; S does not have to be even
                self.expected_symbols.append(TbiR(even=False))
                pass
            pass
        # We don't log the I after a packet
        # self.expected_symbols.append(TbiK(even=True, optional=True))
        for i in range(ipg):
            self.gmii_tx_enable.wait_for_value(1)
            self.gmii_tx__tx_en.drive(0)
            self.gmii_tx__tx_er.drive(0)
            self.bfm_wait(1)
            pass
        pass
    #f run__finalize
    def run__finalize(self):
        self.bfm_wait(100)
        self.gmii_tx_check_expected_data()
        self.compare_expected("Expected data is empty",len(self.expected_symbols),0)
        super(SgmiiTest_GmiiTx_Base,self).run__finalize()
        pass
        
    #f All done
    pass
#c SgmiiTest_GmiiTx_0
class SgmiiTest_GmiiTx_0(SgmiiTest_GmiiTx_Base):
    #f run
    def run(self):
        self.gmii_tx_pkt([1,2,3,4,5,6])
        self.gmii_tx_pkt([1,2,3,4])
        self.gmii_tx_pkt([1,2,3,4,5])
        self.gmii_tx_pkt([1,2,3,4])
        self.gmii_tx_pkt([1,2,3,4,5])
        self.gmii_tx_pkt([1,2,3,4,5])
        self.gmii_tx_pkt([1,2,3,4])
        self.gmii_tx_pkt([1,2,3,4,5])
        self.gmii_tx_pkt([1,2,3,4,5])
        pass

#c SgmiiTest_GmiiTx_1
class SgmiiTest_GmiiTx_1(SgmiiTest_GmiiTx_Base):
    #f run
    def run(self):
        # def gmii_tx_pkt(self, data, error_data=0, carrier_extend=0, ipg=8):
        self.gmii_tx_pkt([1,2,3,4,5,6], error_data=5)
        self.gmii_tx_pkt([1,2,3,4])
        self.gmii_tx_pkt([1,2,3,4,5], error_data=5)
        self.gmii_tx_pkt([1,2,3,4])
        self.gmii_tx_pkt([1,2,3,4,5], error_data=2)
        self.gmii_tx_pkt([1,2,3,4,6], error_data=2)
        self.gmii_tx_pkt([1,2,3,4])
        self.gmii_tx_pkt([1,2,3,4,5], error_data=5)
        pass

#c SgmiiTest_GmiiTx_2
class SgmiiTest_GmiiTx_2(SgmiiTest_GmiiTx_Base):
    #f run
    def run(self):
        # def gmii_tx_pkt(self, data, error_data=0, carrier_extend=0, ipg=8):
        self.gmii_tx_pkt([1,2,3,4,5,6], carrier_extend=4)
        self.gmii_tx_pkt([1,2,3,4])
        self.gmii_tx_pkt([1,2,3,4,6], error_data=2)
        self.gmii_tx_pkt([1,2,3,4])
        self.gmii_tx_pkt([1,2,3,4,5], error_data=5)
        self.gmii_tx_pkt([1,2,3,4,5,6], carrier_extend=3)
        self.gmii_tx_pkt([1,2,3,4])
        pass

#c SgmiiTest_GmiiTx_3
class SgmiiTest_GmiiTx_3(SgmiiTest_GmiiTx_Base):
    #f run
    def run(self):
        # def gmii_tx_pkt(self, data, error_data=0, carrier_extend=0, ipg=8):
        self.gmii_tx_pkt([1,2,3,4,5,6], carrier_extend=4)
        self.gmii_tx_pkt([1,2,3,4])
        self.gmii_tx_pkt([1,2,3,4,5,6], carrier_extend=4)
        self.gmii_tx_pkt([1,2,3,4,5,6], carrier_extend=4,ipg=0)
        self.gmii_tx_pkt([1,2,3,4,5],   carrier_extend=4,ipg=0)
        self.gmii_tx_pkt([1,2,3,4,5,6], carrier_extend=4,ipg=2)
        self.gmii_tx_pkt([1,2,3,4,5,6], carrier_extend=3)
        self.gmii_tx_pkt([1,2,3,4])
        pass

#c SgmiiTest_GmiiRx_Base
class SgmiiTest_GmiiRx_Base(SgmiiTest_Base):
    sgmii_module = "dut.sgg"
    pkt_sop     = (1,0,0x55)
    pkt_carrier = (0,1,0x0f)
    #f Stimulus
    class Stimulus(object):
        pass
    class Idle(Stimulus):
        def __init__(self, size):
            self.size=size
            pass
        def action(self, test):
            test.gmii_rx_idle(self.size)
            test.is_idle = True
            pass
        pass
    class Pkt(Stimulus):
        def __init__(self, size, errors=0, error_insert_at=None):
            self.data = range(size)
            self.errors = errors
            self.error_insert_at = error_insert_at
            pass
        def action(self, test):
            if test.is_idle:
                test.gmii_rx_expected.append(test.pkt_sop)
                pass
            else:
                test.gmii_rx_expected.append(test.pkt_carrier)
                pass
            if self.error_insert_at is None:
                for d in self.data:
                    test.gmii_rx_expected.append((1,0,(d&0xff)))
                    pass
                test.gmii_rx_stream([TbiS] + list(self.data) + [TbiV]*self.errors + [TbiT,TbiR], opt_r=True)
                for i in range(self.errors):
                    test.gmii_rx_expected.append((1,1,None))
                    pass
                pass
            else:
                data = list(self.data)
                for d in data[0:self.error_insert_at]:
                    test.gmii_rx_expected.append((1,0,(d&0xff)))
                    pass
                for i in range(self.errors):
                    test.gmii_rx_expected.append((1,1,None))
                    pass
                for d in data[self.error_insert_at:]:
                    test.gmii_rx_expected.append((1,0,(d&0xff)))
                    pass
                test.gmii_rx_stream([TbiS] + data[0:self.error_insert_at])
                test.gmii_rx_stream([TbiV]*self.errors)
                print(data[self.error_insert_at:] + [TbiT,TbiR])
                test.gmii_rx_stream(data[self.error_insert_at:] + [TbiT,TbiR], opt_r=True)
                pass
            test.is_idle = False
            pass
        pass
    #f run__init - invoked by submodules
    def run__init(self):
        self.bfm_wait(10)
        self.expected_symbols = []
        self.even = True
        self.disparity = 1
        self.gmii_symbols = {}
        self.gmii_datas = {}
        self.log_data         = self.log_recorder(self.sgmii_module)
        self.log_data_parser  = RxGmiiLogParser()
        self.write_sgmii_control(0,7)
        self.write_sgmii_control(0,3)
        pass
    #f gmii_rx_encoding
    def gmii_rx_encoding(self, ei):
        e = ei.encoding_p
        if self.disparity!=0: e = ei.encoding_n
        self.disparity = e.disparity_out
        self.even = not self.even
        self.tbi_rx__valid.drive(1)
        self.tbi_rx__data.drive(e.encoding)
        self.bfm_wait(1)
        self.tbi_rx__valid.drive(0)
        pass
    #f gmii_rx_symbol
    def gmii_rx_symbol(self, s):
        if s not in self.gmii_symbols:
            self.gmii_symbols[s] = s()
            pass
        self.gmii_rx_encoding(self.gmii_symbols[s])
        pass
    #f gmii_rx_data
    def gmii_rx_data(self, d):
        if d not in self.gmii_datas:
            self.gmii_datas[d] = TbiD(d)
            pass
        self.gmii_rx_encoding(self.gmii_datas[d])
        pass
    #f gmii_rx_idle
    def gmii_rx_idle(self, count):
        if not self.even:
            self.verbose.error("Have to put out even before idle - should already be even")
            self.gmii_rx_data((2<<5) | 16)
            pass
        for i in range(count):
            if self.disparity==0:
                self.gmii_rx_symbol(TbiK)
                self.gmii_rx_data((2<<5) | 16)
                pass
            else:
                self.gmii_rx_symbol(TbiK)
                self.gmii_rx_data((6<<5) | 5)
                pass
            pass
        if self.disparity!=0:
            self.verbose.error("Parity must be negative after idle")
            pass
        pass
    #f gmii_rx_stream
    def gmii_rx_stream(self, stream, opt_r=False):
        for s in stream:
            if type(s) is int:
                self.gmii_rx_data(s)
                pass
            else:
                self.gmii_rx_symbol(s)
                pass
            pass
        if opt_r and (not self.even):
            self.gmii_rx_symbol(TbiR)
            pass
        pass
    #f gmii_rx_check_expected_data
    def gmii_rx_check_expected_data(self):
        while (self.log_data.num_events()!=0) and (self.expected_symbols!=[]):
            l = self.log_data_parser.parse_log_event(self.log_data.event_pop())
            if l is None: continue
            while True:
                if self.expected_symbols==[]: raise Exception("expected_symbols was empty - can only occur if an optional symbol is at the end of the list, which is a bug")
                sym = self.expected_symbols.pop(0)
                (err,opt) = sym.check_with_log(l)
                if (not err) or (not opt): break
                pass
            if err:
                self.failtest("Symbol mismatch in rx data check (log %s symbol %s)"%(str(l),str(sym)))
                pass
            pass
        pass
    #f gmii_rx_pkt
    def gmii_rx_pkt(self, data, error_data=0, carrier_extend=0, ipg=8):
        """
        Assumes that any idle is properly complete
        """
        self.gmii_rx_symbol(RxS)
        self.expected_symbols.append(TbiS())
        dn = 0
        for d in data:
            if dn>0: self.expected_symbols.append(TbiD(d,optional=(dn==1)))
            dn = dn + 1
            self.gmii_rx_enable.wait_for_value(1)
            self.gmii_rx__rx_en.drive(1)
            self.gmii_rx__rx_er.drive(0)
            self.gmii_rx__rxd.drive(d)
            self.bfm_wait(1)
            pass
        for i in range(error_data):
            self.expected_symbols.append(TbiV())
            self.gmii_rx_enable.wait_for_value(1)
            self.gmii_rx__rx_en.drive(1)
            self.gmii_tx__tx_er.drive(1)
            self.bfm_wait(1)
            pass
        self.expected_symbols.append(TbiT())
        if carrier_extend==0:
            self.expected_symbols.append(TbiR(even=True, optional=True))
            self.expected_symbols.append(TbiR(even=False))
            pass
        else:
            cn = 0
            for i in range(carrier_extend):
                # one cycle provides T, one for the R at the end
                if (cn>=1): self.expected_symbols.append(TbiR())
                cn = cn + 1
                self.gmii_tx_enable.wait_for_value(1)
                self.gmii_tx__txd.drive(0xf)
                self.gmii_tx__tx_en.drive(0)
                self.gmii_tx__tx_er.drive(1)
                self.bfm_wait(1)
                pass
            self.expected_symbols.append(TbiR(even=True, optional=True))
            if ipg>0: # if ipg is 0 then we have added enough cycles; S does not have to be even
                self.expected_symbols.append(TbiR(even=False))
                pass
            pass
        # We don't log the I after a packet
        # self.expected_symbols.append(TbiK(even=True, optional=True))
        for i in range(ipg):
            self.gmii_tx_enable.wait_for_value(1)
            self.gmii_tx__tx_en.drive(0)
            self.gmii_tx__tx_er.drive(0)
            self.bfm_wait(1)
            pass
        pass
    #f run
    def run(self):
        self.gmii_rx_expected = []
        is_idle = False
        # Wait and clear log queue - as the config/autonegotiation data will be in the log
        for x in self.stimulus:
            x.action(self)
            pass
        self.bfm_wait(1)
        while self.log_data.num_events()!=0:
            l = self.log_data_parser.parse_log_event(self.log_data.event_pop())
            if l is None: continue
            if self.gmii_rx_expected==[]:
                self.failtest("Extra GMII received when none expected %s"%(str(l)))
                pass
            else:
                (dv, er, d) = self.gmii_rx_expected.pop(0)
                self.compare_expected("dv in gmii rx data (log %s)"%(str(l)), dv, l.dv)
                self.compare_expected("er in gmii rx data (log %s)"%(str(l)), er, l.er)
                if d is not None:
                    self.compare_expected("data in gmii rx data (log %s)"%(str(l)), d, l.data)
                    pass
                pass
            pass
        pass
    #f run__finalize
    def run__finalize(self):
        self.bfm_wait(100)
        self.gmii_rx_check_expected_data()
        self.compare_expected("Expected data is empty",len(self.expected_symbols),0)
        super(SgmiiTest_GmiiRx_Base,self).run__finalize()
        pass
        
    #f All done
    pass
#c SgmiiTest_GmiiRx_0
class SgmiiTest_GmiiRx_0(SgmiiTest_GmiiRx_Base):
    Idle = SgmiiTest_GmiiRx_Base.Idle
    Pkt = SgmiiTest_GmiiRx_Base.Pkt
    stimulus = [ Idle(32), Pkt(8), Idle(32), Pkt(4), Idle(32) ]

#c SgmiiTest_GmiiRx_1
class SgmiiTest_GmiiRx_1(SgmiiTest_GmiiRx_Base):
    Idle = SgmiiTest_GmiiRx_Base.Idle
    Pkt = SgmiiTest_GmiiRx_Base.Pkt
    stimulus = [ Idle(32), Pkt(8), Pkt(4), Pkt(8), Pkt(4), Pkt(8), Pkt(4), Idle(32) ]

#c SgmiiTest_GmiiRx_2
class SgmiiTest_GmiiRx_2(SgmiiTest_GmiiRx_Base):
    Idle = SgmiiTest_GmiiRx_Base.Idle
    Pkt = SgmiiTest_GmiiRx_Base.Pkt
    stimulus = [ Idle(32), Pkt(8, errors=5), Idle(32) ]

#c SgmiiTest_GmiiRx_3
class SgmiiTest_GmiiRx_3(SgmiiTest_GmiiRx_Base):
    Idle = SgmiiTest_GmiiRx_Base.Idle
    Pkt = SgmiiTest_GmiiRx_Base.Pkt
    stimulus = [ Idle(32), Pkt(8, errors=1, error_insert_at=3), Idle(32) ]

#a Hardware classes
#c SgmiiHw
class SgmiiHw(HardwareThDut):
    clock_desc = [("clk",(0,1,1)),
    ]
    reset_desc = {"name":"reset_n", "init_value":0, "wait":5}
    module_name = "tb_sgmii"
    dut_inputs  = {"gmii_tx":t_gmii_tx,
                   "sgmii_rxd":4,
                   "tbi_rx" :t_tbi_valid,
                   "sgmii_gasket_control":t_sgmii_gasket_control,
    }
    dut_outputs = {"gmii_tx_enable":1,
                   "sgmii_txd":4,
                   "tbi_tx":t_tbi_valid,
                   "gmii_rx":t_gmii_rx,
                   "gmii_rx_enable":1,
                   "sgmii_gasket_status":t_sgmii_gasket_status,
    }
    loggers = {
        "gmii":{"modules":"dut.sgg", "verbose":0, "filename":"gmii.log"},
        }
    pass

#a Simulation test classes
#c Sgmii
class Sgmii(TestCase):
    hw = SgmiiHw
    kwargs = {
     # "verbosity":0,
        }
    _tests = {
        "gmii_tx_0"  : (SgmiiTest_GmiiTx_0, 8*1000,  kwargs),
        "gmii_tx_1"  : (SgmiiTest_GmiiTx_1, 8*1000,  kwargs),
        "gmii_tx_2"  : (SgmiiTest_GmiiTx_2, 8*1000,  kwargs),
        "gmii_tx_3"  : (SgmiiTest_GmiiTx_3, 8*1000,  kwargs),
        "gmii_rx_0"  : (SgmiiTest_GmiiRx_0, 8*1000,  kwargs),
        "gmii_rx_1"  : (SgmiiTest_GmiiRx_1, 8*1000,  kwargs),
        "gmii_rx_2"  : (SgmiiTest_GmiiRx_2, 8*1000,  kwargs),
        "gmii_rx_3"  : (SgmiiTest_GmiiRx_3, 8*1000,  kwargs),
        "smoke"  : (SgmiiTest_GmiiRx_2, 8*1000,  kwargs),
    }
    pass

