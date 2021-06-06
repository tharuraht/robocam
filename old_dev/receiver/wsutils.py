#https://gist.github.com/pocc/2c89dd92d6a64abca3db2a29a11f1404
"""
Pcap class to more easily interact with pcaps
When in doubt, aim for simplicity of requests API
Like pyshark, but for the wireshark utilities
"""
import os
import subprocess as sp
import re
import pprint
import tempfile
import shutil
import sys

class Pcap:
    """
    Pcap wrapper around wireshark functionality. Call pcap utils if there
    are multiple files.
    """
    def __init__(self, filename):
        self.filename = os.path.expanduser(filename)
        self.info = self.get_capinfos([self.filename])

    @staticmethod
    def get_capinfos(filenames):
        """Get a dict from a packet using Wireshark's capinfos.

        Args:
            filenames (list): List of full filepaths to get info for
        Returns:
            (dict) of info about files
                {
                    "/path/to/file1": {"key": "value", ...},
                    ...
                }
        """
        cmd_list = ["capinfos", "-M"] + filenames
        output = sp.run(cmd_list, stdout=sp.PIPE, stderr=sp.DEVNULL).stdout.decode('utf-8') #modified from check_output
        data = re.findall(r'(.+?):\s*([\s\S]+?)(?=\n[\S]|$)', output)
        infos_dict = {i[0]: i[1] for i in data}
        for key in infos_dict:
            if 'Interface #' in key:
                iface_infos = re.findall(r'\s*(.+?) = (.+)\n', infos_dict[key])
                infos_dict[key] = {i[0]: i[1] for i in iface_infos}

        return infos_dict

    def reorder(self):
        """Wrapper for reordercap

        Returns:
            (int) Quantity of out of order packets that have been fixed
        """
        with tempfile.NamedTemporaryFile() as temp_file:
            cmd_list = ["reordercap", "-n", self.filename, temp_file.name]
            output = sp.check_output(cmd_list).decode('utf-8')
            out_of_order = int(re.findall(r"[\d]+ .*?, ([\d]+) .*", output)[0])

            if out_of_order > 0:
                shutil.copy(temp_file.name, self.filename)

        return out_of_order


def merge(filenames, outfile, outfmt="", ordered=True, idb_mode="", snaplen=0):
    """Merge one or more files using Wireshark's mergecap utility

    Args:
        filenames (list): List of files to merge
        outfile (str): Filepath to write combined file (mergecap -w)
        outfmt (str): Output file format, default is pcapng (mergecap -F)
        ordered (bool): Whether to reorder all packets based on timestamp
            after merge (~= mergecap -a)
        idb_mode (str): How/If to combine Interface Description Blocks
            One of 'B<none>', 'B<all>', or 'B<any>' (~= mergecap -I <IDB>)
        snaplen (int): Truncate packets to <num> bytes (~= mergecap -s <num>)
    Returns:
        (str): Any output that mergecap provides
    """
    cmd_list = ["mergecap"] + filenames + ["-w", outfile]
    if outfmt:
        cmd_list += ["-F", outfmt]
    if not ordered:
        cmd_list += ["-a"]
    if idb_mode:
        cmd_list += ["-i", idb_mode]
    if snaplen:
        cmd_list += ["-s", snaplen]

    return sp.check_output(cmd_list).decode('utf-8')

# assert(len(sys.argv) >= 2), 'length is %0d' % len(sys.argv)

# for i in range(1,len(sys.argv)):
#     mypcap = Pcap(sys.argv[i])
#     txt =mypcap.info['Data bit rate']
#     res = re.findall(r'\d+\.\d+',txt)
#     #print(txt)
#     print(res)
    

    #pprint.pprint(mypcap.info)
#print(mypcap.reorder())
   
