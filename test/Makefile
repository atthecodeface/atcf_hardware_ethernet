Q=@
CDL_REGRESS = ${CDL_ROOT}/libexec/cdl/cdl_regress.py

SMOKE_OPTIONS = --only-tests 'smoke'
SMOKE_TESTS   = test_8b10b test_sgmii
SMOKE_TESTS   = test_sgmii
REGRESS_TESTS = test_8b10b test_sgmii
CDL_REGRESS_PACKAGE_DIRS = --package-dir regress:${SRC_ROOT}/python  --package-dir regress:${GRIP_ROOT_PATH}/atcf_hardware_apb/python

.PHONY:smoke
smoke:
	${CDL_REGRESS} --pyengine-dir=${BUILD_ROOT} ${CDL_REGRESS_PACKAGE_DIRS} --suite-dir=python ${SMOKE_OPTIONS} ${SMOKE_TESTS}

.PHONY:regress
regress:
	${CDL_REGRESS} --pyengine-dir=${BUILD_ROOT} ${CDL_REGRESS_PACKAGE_DIRS} --suite-dir=python ${REGRESS_TESTS}
