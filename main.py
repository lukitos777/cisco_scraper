from paramiko import SSHClient, AutoAddPolicy
from dotenv import load_dotenv

from re import findall, match, split
from csv import writer
from json import dump
from os import getenv

# main.py file's structure :
# main.py
# |---- get_int_status         |<function>
# |---- parse_loopback_output  |<function>
# |---- get_switch_info        |<function>
# |---- write_interface_status |<function>
# |---- write_mac_address      |<function>
# |---- write_ip_arp           |<function>
# |---- send_data              |<function> not implemented!
# |---- main                   |<function> entery point of the scrypt

def get_int_status(hostname: str, username: str, password: str) -> list[str]:
    try:
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())

        client.connect(hostname=hostname, username=username, password=password)

        commands = [
            'show int status | i connected',
            'show int status | exc connected',
            'show mac adrdress-table',
            'show ip arp'
        ]
        
        data: list[str] = []

        for command in commands:
            stdin, stdout, stderr = client.exec_command(command=command)

            data.append(stdout.read().decode())
            error = stderr.read().decode()

            if error:
                print(f'Error executing "{command}" error -> "{error}"')
                return []

    except Exception as e:
        print(f'Exception {e}')
        return []
    finally:
        client.close()

    return data


# fucntion to convert loopback data into the dictionary
# Interface              IP-Address      OK? Method Status                Protocol
# Loopback0              192.168.1.1     YES unset  up                    up
# Loopback1              10.1.1.1        YES unset  up                    up
# this will be converted into the
# {'Loopback0': '192.168.1.1', 'Loopback1': '10.1.1.1'}
def parse_loopback_output(output: str) -> dict[str, str]:
    loopback_dict: dict[str, str] = {}

    lines = output.strip().split('\n')
    
    for line in lines:
        match_ = match(r'(\S+)\s+([\d.]+)', line)

        if match_:
            interface = match_.group(1)
            ip_address = match_.group(2)
            loopback_dict[interface] = ip_address
    
    return loopback_dict


def get_switch_info(hostname: str, username: str, password: str) -> dict[str, str]:
    try:
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())

        client.connect(hostname=hostname, username=username, password=password)

        # excpected result | cisco command
        commands = {
            'switch_name': 'show running-config | include hostname',
            'loopback_ip': 'show ip interface brief | include Loopback',
            'version': 'show version',
            'model': 'show version | include Model',
            'interface_count': 'show ip interface brief'
        }

        results: dict[str, str | list[str] | dict[str, str] | int] = {}

        for key, command in commands.items():
            stdin, stdout, stderr = client.exec_command(command)

            output = stdout.read().decode()
            error = stderr.read().decode()

            if key == 'switch_name':
                results[key] = output.split()[1] if output else 'N/A'
            elif key == 'loopback_ip':
                results[key] = parse_loopback_output(output)
            elif key == 'version':
                results[key] = output
            elif key == 'model':
                results[key] = findall(r'Model number\s+: (.+)', output)
            elif key == 'interface_count':
                results[key] = len(output.strip().split('\n')) - 1

            if error:
                print(f'Error executing "{command}" error -> "{error}"')
                return {}

    except Exception as e:
        print(f'Exception: {e}')
        return {}
    finally:
        client.close()

    return results


def write_interface_status(connected_output: str, disconnected_output: str) -> None:
    connected_lines = connected_output.strip().split('\n')

    with open('connected_interfaces.csv', mode='w', newline='') as connected_file:
        connected_writer = writer(connected_file)
        connected_writer.writerow(['Port', 'Status', 'VLAN', 'Duplex', 'Speed', 'Type'])

        for line in connected_lines[1:]:
            parts = split(r'\s{2,}', line)
            connected_writer.writerow(parts[1:])

    disconnected_lines = disconnected_output.strip().split('\n')

    with open('disconnected_interfaces.csv', mode='w', newline='') as disconnected_file:
        disconnected_writer = writer(disconnected_file)
        disconnected_writer.writerow(['Port', 'Status', 'VLAN', 'Duplex', 'Speed', 'Type'])

        for line in disconnected_lines[1:]:
            parts = split(r'\s{2,}', line)
            disconnected_writer.writerow(parts[1:])


def write_mac_address(mac_addsress_table: str) -> None:
    lines = mac_addsress_table.strip().split('\n')
    csv_data = []

    for line in lines[2:-1]:
        parts = line.split()
        if len(parts) >= 4:
            csv_data.append([*parts])

    if csv_data:
        with open('mac_address_table.csv', 'w', newline='') as file:
            csv_writer = writer(file)
            csv_writer.writerow(['Vlan', 'Mac Address', 'Type', 'Ports'])
            csv_writer.writerows(csv_data)


def write_ip_arp(table: str) -> None:
    lines = table.strip().split('\n')
    csv_data = []

    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 5:
            interface = parts[-1]
            ip_address = parts[1]
            mac_address = parts[3]
            csv_data.append([interface, mac_address, ip_address])

    if csv_data:
        with open('ip_arp_table.csv', 'w', newline='') as file:
            csv_writer = writer(file)
            csv_writer.writerow(['Interface', 'MAC Address', 'IP Address']) 
            csv_writer.writerows(csv_data)


# this function sends data to the sys-admin
# and then clears data files
def send_data() -> None:
    # send data to sys-admyn

    with open('connected_interfaces.csv', 'w', newline='') as file: pass
    with open('disconnected_interfaces.csv', 'w', newline='') as file: pass
    with open('ip_arp_table.csv', 'w', newline='') as file: pass
    with open('mac_address_table.csv', 'w', newline='') as file: pass

    with open('switch_data.json', 'w') as file: file.write('[]')   


def main(*args, **kwargs) -> None:
    load_dotenv()

    host, user, password = getenv('HOST'), getenv('USER'), getenv('PASS')

    table_data = get_int_status(hostname=host, username=user, password=password)

    # writing the result of the commands:
    # < show int status | i connected >, < show int status | exc connected >
    # < show mac address-table > & < show ip arp >
    # into the csv files 
    if table_data:
        write_interface_status(table_data[0], table_data[1])
        write_mac_address(table_data[2])
        write_ip_arp(table_data[3])

    switch_info = get_switch_info(hostname=host, username=user, password=password)

    # here we converting data about the switch into the json file
    # here are switch name, loopback ips, switch versions, models 
    # and number of interfaces
    if switch_info:
        with open('switch_data.json', 'w') as json_file:
            dump(switch_info, json_file)

    send_data()

if __name__ == '__main__':
    main()
    