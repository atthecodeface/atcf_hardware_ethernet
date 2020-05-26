import cdl_desc
from cdl_desc import CdlModule, CdlSimVerilatedModule, CModel, CSrc

class Library(cdl_desc.Library):
    name="ethernet"
    pass

class GbEModules(cdl_desc.Modules):
    name = "gigabit"
    src_dir      = "cdl"
    tb_src_dir   = "tb_cdl"
    libraries = {"std":True, "utils":True, "analyzer":True, "clocking":True, "networking":True}
    cdl_include_dirs = ["cdl"]
    export_dirs = cdl_include_dirs + [ src_dir ]
    modules = []
    modules += [ CdlModule("decode_8b10b") ]
    modules += [ CdlModule("encode_8b10b") ]
    modules += [ CdlModule("gbe_axi4s32") ]
    modules += [ CdlModule("gbe_single") ]
    modules += [ CdlModule("sgmii_gmii_gasket") ]
    modules += [ CdlModule("sgmii_transceiver") ]
    modules += [ CdlModule("tb_sgmii", src_dir=tb_src_dir) ]
    modules += [ CdlModule("tb_gbe", src_dir=tb_src_dir) ]
    pass

