from dotenv import load_dotenv

from json import load
from csv import reader
from os import getenv
import unittest

from main import (
    get_int_status, get_switch_info, parse_loopback_output, send_data,
    write_ip_arp, write_mac_address, write_interface_status
)

# test.py file's structure
# test.py 
# Test_Scrypt                      | <class>
# |---- setUp                      | <method>
# |     |---- user_fake            | <atribute>
# |     |---- password_fake        | <atribute>
# |     |---- host_fake            | <atribute>
# |     |---- host                 | <atribute>
# |     |---- user                 | <atribute>
# |     |---- password             | <atribute>
# |---- test_get_int_status_1      | <method>
# |---- test_get_int_status_2      | <method>
# |---- test_get_switch_info_1     | <method>
# |---- test_get_switch_info_2     | <method>
# |---- test_parse_lookback_output | <method>
# |---- test_write_interface_status| <method>
# |---- test_write_ip_arp          | <method>
# |---- test_write_mac_address     | <method>
# |---- test_send_data             | <method>

class Test_Scrypt(unittest.TestCase):

    def setUp(self) -> None:
        self.user_fake = 'USER'
        self.password_fake = 'PASS'
        self.host_fake = 'HOST'
        
        load_dotenv()

        self.host, self.user, self.password = getenv('HOST'), getenv('USER'), getenv('PASS')
    
    # testing with fake data
    def test_get_int_status_1(self):
        res = get_int_status(
            username=self.user_fake, hostname=self.host_fake, password=self.password_fake
        )

        self.assertEqual(res, [])

    # testing with valid user, password & host
    def test_get_int_status_2(self):
        # TODO
        self.assertEqual(True, True)

    def test_get_switch_info_1(self):
        res = get_switch_info(
            username=self.user_fake, hostname=self.host_fake, password=self.password_fake
        )

        self.assertEqual(res, {})

    def test_get_switch_info_2(self):
        # TODO
        self.assertEqual(True, True)

    def test_parse_loopback_output(self):
        res = parse_loopback_output(
            output='Loopback0              192.168.1.1     YES unset  up                    up\nLoopback1              10.1.1.1        YES unset  up                    up'
        )

        self.assertEqual(
            res, {'Loopback0': '192.168.1.1', 'Loopback1': '10.1.1.1'}
        )

    def test_write_interface_status(self):
        connected_test_output = """Port      Name               Status       Vlan       Duplex  Speed Type
                                    Fa0/1                      connected    10         a-full  a-100  10/100BaseTX
                                    Fa0/2                      connected    20         a-full  a-100  10/100BaseTX
                                    Gi0/1                      connected    trunk      a-full  a-1000  1000BaseLX
                                """
        
        disconnected_test_output = """Port      Name               Status       Vlan       Duplex  Speed Type
                                        Fa0/3                      notconnect   10         auto    auto  10/100BaseTX
                                        Fa0/4                      administratively down  1      auto    auto  10/100BaseTX
                                        Gi0/2                      notconnect   1          auto    auto  1000BaseSX
                                    """
        
        expected_res_1 = [
            ['Port', 'Status', 'VLAN', 'Duplex', 'Speed', 'Type'],
            ['Fa0/1', 'connected', '10', 'a-full', 'a-100', '10/100BaseTX'],
            ['Fa0/2', 'connected', '20', 'a-full', 'a-100', '10/100BaseTX'],
            ['Gi0/1', 'connected', 'trunk', 'a-full', 'a-1000', '1000BaseLX']
        ]
        
        expected_res_2 = [
            ['Port', 'Status', 'VLAN', 'Duplex', 'Speed', 'Type'],
            ['Fa0/3', 'notconnect', '10', 'auto', 'auto', '10/100BaseTX'],
            ['Fa0/4', 'administratively down', '1', 'auto', 'auto', '10/100BaseTX'],
            ['Gi0/2', 'notconnect', '1', 'auto', 'auto', '1000BaseSX'],
        ]

        write_interface_status(connected_output=connected_test_output, disconnected_output=disconnected_test_output)
        connected_data, disconnected_data = [], []

        with open('connected_interfaces.csv', 'r', newline='') as file:
            data_vcs = reader(file)

            for row in data_vcs:
                connected_data.append(row)

        with open('disconnected_interfaces.csv', 'r', newline='') as file:
            data_vcs = reader(file)

            for row in data_vcs:
                disconnected_data.append(row)

        self.assertEqual(
            (connected_data == expected_res_1) and (disconnected_data == expected_res_2), True
        )
        

    def test_write_ip_arp(self):
        test_output = """Protocol  Address          Age (min)  Hardware Address  Type  Interface
                        Internet  192.168.1.1      10         00:1A:2B:3C:4D:5E  ARPA  FastEthernet0/0
                        Internet  192.168.1.2      5          00:1A:2B:3C:4D:5F  ARPA  FastEthernet0/0
                        Internet  192.168.1.3      3          00:1A:2B:3C:4D:60  ARPA  FastEthernet0/1
                        Internet  192.168.1.4      1          00:1A:2B:3C:4D:61  ARPA  FastEthernet0/1
                        """
        write_ip_arp(test_output)
        data = []

        with open('ip_arp_table.csv', 'r', newline='') as file:
            data_vcs = reader(file)

            for row in data_vcs:
                data.append(row)

        self.assertEqual(
            data, 
            [
                ['Interface', 'MAC Address', 'IP Address'],
                ['FastEthernet0/0', '00:1A:2B:3C:4D:5E', '192.168.1.1'],
                ['FastEthernet0/0', '00:1A:2B:3C:4D:5F', '192.168.1.2' ],
                ['FastEthernet0/1', '00:1A:2B:3C:4D:60', '192.168.1.3'],
                ['FastEthernet0/1', '00:1A:2B:3C:4D:61', '192.168.1.4']
            ]
        )

    def test_write_mac_address(self):
        test_output = """Vlan    Mac Address       Type        Ports
                        ----    -----------       --------    -----
                        10    00:1A:2B:3C:4D:5E  DYNAMIC     Fa0/1
                        10    00:1A:2B:3C:4D:5F  DYNAMIC     Fa0/2
                        20    00:1A:2B:3C:4D:60  DYNAMIC     Fa0/3
                        30    00:1A:2B:3C:4D:61  DYNAMIC     Fa0/4
                        1     00:1A:2B:3C:4D:62  DYNAMIC     Gi0/1
                        Total Mac Addresses for this criterion: 5
                    """
        
        write_mac_address(test_output)
        data = []

        with open('mac_address_table.csv', 'r', newline='') as file:
            data_csv = reader(file)

            for row in data_csv:
                data.append(row)

        self.assertEqual(
            data, 
            [
                ['Vlan', 'Mac Address', 'Type', 'Ports'],
                ['10', '00:1A:2B:3C:4D:5E', 'DYNAMIC', 'Fa0/1'],
                ['10', '00:1A:2B:3C:4D:5F', 'DYNAMIC', 'Fa0/2'],
                ['20', '00:1A:2B:3C:4D:60', 'DYNAMIC', 'Fa0/3'],
                ['30', '00:1A:2B:3C:4D:61', 'DYNAMIC', 'Fa0/4'],
                ['1', '00:1A:2B:3C:4D:62', 'DYNAMIC', 'Gi0/1']
            ]
        )


    def test_send_data(self):
        inf: list[int] = []

        send_data()

        with open('connected_interfaces.csv', 'r', newline='') as file:
            data = reader(file)
            if not any(data):
                inf.append(True)

        with open('disconnected_interfaces.csv', 'r', newline='') as file:
            data = reader(file)
            if not any(data):
                inf.append(True)

        with open('ip_arp_table.csv', 'r', newline='') as file:
            data = reader(file)
            if not any(data):
                inf.append(True)

        with open('mac_address_table.csv', 'r', newline='') as file:
            data = reader(file)
            if not any(data):
                inf.append(True)

        with open('switch_data.json', 'r') as file:
            data = load(file)
            if not data:
                inf.append(True)

        self.assertEqual(all(inf), True)
        