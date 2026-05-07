from packaging.version import parse
import requests
import unittest

from mock import MagicMock, patch

from nextdrawcore import nextdraw
from nextdrawcore.nextdraw_options import versions
from nextdrawcore.nextdraw_options.versions import (
        DEV_NEXTDRAW_CONTROL, NEXTDRAW_CONTROL, EBB_FIRMWARE)
from nextdrawcore.plot_status import PlotStatus

from plotink import ebb_serial

from .. import MessageAssertionMixin, set_up_nextdraw_with_args

from plotink.plot_utils_import import from_dependency_import # plotink
message = from_dependency_import('ink_extensions_utils.message')

# python -m unittest discover in top-level package dir

web_versions = {'Hershey Advanced': '1.0.0',
                'Hershey Advanced (unstable)': '2.0.0',
                NEXTDRAW_CONTROL: '10.0.0',
                DEV_NEXTDRAW_CONTROL: '11.0.0',
                EBB_FIRMWARE: '100.0.0',
                'Some Other Software Version': 'ectoplasm'}
get_ret_value = MagicMock()
get_ret_value.text = repr(web_versions)

@patch.object(versions.requests, "get", return_value = get_ret_value)
@patch.object(versions, "logger")
class ReportVersionInfoTestCase(unittest.TestCase, MessageAssertionMixin):
    '''see test/test_integration for more relevant tests'''

    @staticmethod
    def _construct_default_params():
        ''' utility for setting up the many params for calling report_version_info '''
        nd = set_up_nextdraw_with_args(['--model=8'])
        nd.user_message_fun = MagicMock()
        return {
           'nd_ref': nd,
           'message_fun': nd.user_message_fun,
        }

    @patch.object(nextdraw.ebb3_serial.EBB3, "query", return_value = "2,13")
    def test_report_version_info(self, m_logger, _, __):
        '''
        testing the most basic case for report_version_info:
        * an NextDraw is connected and the firmware version is the most up-to-date
        * internet is available and the current version matches the "stable" version
        '''
        params = self._construct_default_params()
        params['nd_ref'].version_string = web_versions[NEXTDRAW_CONTROL]
        params['nd_ref'].machine.version = web_versions[EBB_FIRMWARE]
        params['nd_ref'].machine.version_parsed = parse(web_versions[EBB_FIRMWARE])
        params['nd_ref'].machine.port = MagicMock()
        versions.report_version_info(**params)

        m_logger.error.assert_not_called()
        # e.g. "This is NextDraw Control version 10.0.0."
        self.assertAnyMessageContains(params["message_fun"],
                ["NextDraw", "version", web_versions[NEXTDRAW_CONTROL]])
        # e.g. "Your NextDraw Control software is up to date."
        self.assertAnyMessageContains(params["message_fun"],
                ["NextDraw", "up", "date"])
        # e.g. "Your firmware is up to date; no updates are available.\n"
        self.assertAnyMessageContains(params["message_fun"],
                ["firmware", "up", "date"])
        # Also as part of normal function,
        # report_version_info outputs some information about voltage/current
        # e.g. 'Voltage readout: {voltage:d} (~ {scaled_voltage:.2f} V).'
        self.assertAnyMessageContains(params["message_fun"], ["voltage", "2"])
        # e.g. 'Current setpoint: {current:d} (~ {scaled_current:.2f} A).
        self.assertAnyMessageContains(params["message_fun"], ["current", "13"])

    def test_report_version_info__disabled_online_version_checking(self, m_logger, _):
        '''
        testing the case where `check_updates` is set to False (e.g. in the conf.py file)
        '''
        params = self._construct_default_params()
        params['nd_ref'].params.check_updates = False       

        versions.report_version_info(**params)

        # e.g. "Note: Online version checking disabled."
        self.assertAnyMessageContains(params["message_fun"], ["version", "check", "disabled"])

        # The following should be printed even if online version checking is disabled
        # e.g. "This is NextDraw Control version 10.0.0"
        self.assertAnyMessageContains(params["message_fun"], ["NextDraw", "version"])
        m_logger.error.assert_not_called()

    def test_report_version_info__preview(self, m_logger, _):
        '''
        testing the case where `preview` is set to True
        '''
        params = self._construct_default_params()
        params['nd_ref'].machine.port = None
        params['nd_ref'].options.preview = True

        versions.report_version_info(**params)

        # e.g. "\nFirmware version readout not available in preview mode."
        self.assertAnyMessageContains(params["message_fun"],
                ["firmware", "version", "not available", "preview"])
        m_logger.error.assert_not_called()

    def test_report_version_info__fw_update_available(self, _, __):
        params = self._construct_default_params()
        params['nd_ref'].machine.version = "0" # really low, needs updating
        params['nd_ref'].machine.port = MagicMock()

        versions.report_version_info(**params)

        # e.g., 'An update is available to a newer version, 3.9.4.'
        self.assertAnyMessageContains(params["message_fun"],
                ["firmware", "update", "available"])

    def test_report_version_info__dev_software_newest(self, _, __):
        '''
        testing the case where the current software is an early-release/development
        version, and it is the most recent dev version available
        '''
        params = self._construct_default_params()
        params['nd_ref'].version_string  = web_versions[DEV_NEXTDRAW_CONTROL]

        versions.report_version_info(**params)

        # e.g. "~~ An early-release version ~~"
        self.assertAnyMessageContains(params["message_fun"], ["early", "version"])
        # e.g. "This is the newest available development version."
        self.assertAnyMessageContains(params["message_fun"], ["newest", "version", "dev"])
        # e.g. '(The current "stable" release is v. 10.0.0).'
        self.assertAnyMessageContains(params["message_fun"],
                ["current", "stable", web_versions[NEXTDRAW_CONTROL]])

    def test_report_version_info__dev_software_update_available(self, _, __):
        '''
        testing the case where the current software is an early-release/development
        import pdb; pdb.set_trace()
        version, and there are more recent development versions available
        '''
        params = self._construct_default_params()
        params['nd_ref'].version_string = "10.0.1"
        assert parse(params['nd_ref'].version_string) > parse(web_versions[NEXTDRAW_CONTROL])
        assert parse(params['nd_ref'].version_string) < parse(web_versions[DEV_NEXTDRAW_CONTROL])

        versions.report_version_info(**params)

        # e.g. 'An update is available to a newer version, 11.0.0.'
        self.assertAnyMessageContains(params["message_fun"],
                ["update", "available", web_versions[DEV_NEXTDRAW_CONTROL]])
        # e.g. "To update, please contact NextDraw technical support."
        self.assertAnyMessageContains(params["message_fun"], ["update", "contact", "support"])

    def test_report_version_info__software_update_available(self, _, __):
        params = self._construct_default_params()
        params['nd_ref'].version_string = "9.0.0"
        assert parse(params['nd_ref'].version_string) < parse(web_versions[NEXTDRAW_CONTROL])

        versions.report_version_info(**params)

        # e.g. "An update is available to a newer version, 10.0.0."
        self.assertAnyMessageContains(params["message_fun"],
                ["update", "available", web_versions[NEXTDRAW_CONTROL]])
        # e.g. "Please visit: bantam.tools/ndsw for the latest software."
        self.assertAnyMessageContains(params["message_fun"], ["bantam.tools/ndsoft"])

    def test_report_version_info__server_timeout(self, m_logger, m_web_get):
        '''
        testing the case where the request to the version server timed out
        '''
        params = self._construct_default_params()
        m_web_get.side_effect=requests.exceptions.Timeout()

        versions.report_version_info(**params)

        # e.g. "Unable to check for updates online; connection timed out"
        self.assertAnyMessageContains(m_logger.error, ["time", "out"])

    def test_report_version_info__no_server(self, m_logger, m_web_get):
        '''
        testing the case where the version server cannot be contacted
        '''
        params = self._construct_default_params()
        m_web_get.side_effect=requests.exceptions.ConnectionError("this is a test")

        versions.report_version_info(**params)

        # e.g. 'Could not contact server to check for updates. Are you connected to the internet?
        #
        #(Error details: this is a test)'
        self.assertAnyMessageContains(m_logger.error, ["server", "connect", "this is a test"])

    def test_report_version_info__bad_response(self, m_logger, m_web_get):
        '''
        testing the case where there is a problem parsing the server's response
        '''
        valid_text = m_web_get.return_value.text
        try:
            # set up
            params = self._construct_default_params()
            m_web_get.return_value.text = "not a valid response"

            # execute
            versions.report_version_info(**params)

            # test
            # e.g. 'Could not parse server response. This is probably the server's fault.
            #
            # (Error details: {err_info}
            # '
            self.assertAnyMessageContains(m_logger.error, ["server", "parse", "syntax"])
        finally:
            # restore m_web_get mock so it doesn't mess up other tests
            m_web_get.return_value.text = valid_text

class MinFWVersionTestCase(unittest.TestCase):
    def test_min_fw_version(self):
        '''
        rough description of the function's intended behavior:
        if plot_status.fw_version is None, return None;
        otherwise return fw_version>=version_string
        '''

        version_string = "1.0.0"
        test_dict = { # key = plot_status.fw_version; value = expected result
            None: None,
            "1.0.0": True,
            "0.0.5": False,
            "1.0.1": True,
            }

        for fw_version, expected in test_dict.items():
            with self.subTest():
                # set up
                nd_ref = set_up_nextdraw_with_args(['--model=8'])
                nd_ref.machine.version = fw_version
                try:
                    nd_ref.machine.version_parsed = parse(fw_version)
                except:
                    pass
                # run
                actual = versions.min_fw_version(nd_ref, version_string)
                # test
                self.assertEqual(actual, expected,
                    f"Test failed for fw_version set to {nd_ref.machine.version}. "
                    f"Expected {expected}, got {actual}.")
