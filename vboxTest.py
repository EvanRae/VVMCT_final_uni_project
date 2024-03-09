import subprocess
import os
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

def create_vm(vm_name, os_type, iso_path, memory_size, disk_size, disk_format='VDI', disk_location=None, is_64bit=True, vm_folder=None):

    #defining the filepath to VBoxManage as to not assume the user has VBoxManage in their PATH, the VBoxManage path should be the same for all users who do not edit the installation location
    vboxmanage_path = 'C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe'

    cmd = [
        vboxmanage_path,
        'createvm',
        '--name', vm_name,
        '--ostype', os_type + ('_64' if is_64bit else ''), #differentiates between 32bit and 64bit operating systems to allow them both to work
        '--register'
    ]

    #set VM save folder, this will try to create a directory called VirtualMachines in the C drive and will save any created VMs there. if it detects the folder already exists it will call an exception and still save the VMs
    if vm_folder:
        subprocess.run([vboxmanage_path, 'setproperty', 'machinefolder', vm_folder], check=True)
        try:
            os.makedirs(vm_folder)
        except FileExistsError:
            print(f"Directory '{vm_folder}' already exists.")

    
    #run VBox command
    subprocess.run(cmd, check=True)

    #set memory size
    subprocess.run([vboxmanage_path, 'modifyvm', vm_name, '--memory', str(memory_size)], check=True)

    #create the virtual disk
    if disk_location is None:
        disk_location = f'{vm_name}.{disk_format.lower()}'
    subprocess.run([vboxmanage_path, 'createhd', '--filename', disk_location, '--size', str(disk_size)], check=True)

    #attach the ISO
    subprocess.run([vboxmanage_path, 'storagectl', vm_name, '--name', 'IDE Controller', '--add', 'ide'], check=True)
    subprocess.run([vboxmanage_path, 'storageattach', vm_name, '--storagectl', 'IDE Controller', '--port', '0', '--device', '0', '--type', 'dvddrive', '--medium', iso_path], check=True)

    #attach virtual disk, both SATA and IDE are called at the same time to make sure it works regardless of what type of ISO is used, will differentiate later down the line
    subprocess.run([vboxmanage_path, 'storageattach', vm_name, '--storagectl', 'IDE Controller', '--port', '0', '--device', '0', '--type', 'dvddrive', '--medium', iso_path], check=True)
    subprocess.run([vboxmanage_path, 'storageattach', vm_name, '--storagectl', 'SATA Controller', '--port', '0','--device', '0', '--type', 'hdd', '--medium', disk_location], check=True)


#ALL USER INPUTS
vm_name = input("Please name the Virtual Machine: ")
#memory_size = input("Please enter the amount of memory in MB (2048 is recommended): ")
#disk_size = input("Please enter the desired allocated disk space in MB: ")


#allows the user to pick from different ISOs on their system.
file_path = filedialog.askopenfilename(title="Select Image", filetypes=[("ISO Image", ".iso")])


#call create_vm function after taking all user parameters
#current parameters are: vm name, operating system, path to ISO file, memory size in MB, disk size in MB, 64bit, VM folder location
create_vm(vm_name, 'Linux', file_path, 2048, 20000, is_64bit=True, vm_folder=r'C:\\VirtualMachines')


#FOR NOW, RENAME THE VM EVERY TIME YOU CREATE A NEW ONE SO THAT THE PROGRAM DOESNT CRASH

#Current Notes:
#   This has only been tested using an Arch Linux ISO for now, I will be testing Debian, Ubuntu, and Gentoo later and eventually allowing for any OS to be used

#   (So far the vm_folder function does not seem to change where the VMs VDI files are stored as they continue to be saved in VBoxManage's default location (that being C:\Users)
#   vm_folder does manage to create a directory called "VirtualMachines" inside the C drive, however it refuses to save the VDI files in this folder (will research))
#       This has finally been fixed, the base folder of VBoxManage has to be manually overriden in order to save the files to a new directory

#   memory size and disk size variables have been commented out for now, just to allow for easier testing 
#   SATA controller is not found and throws an error, however this does not stop the VM from being created and working, I assume this is because the Arch Linux ISO does not look for SATA connections.

#   (The filepath to the ISOs is currently hardcoded, I will need to find a way to get users to store their ISOs in a default location, or package this program with the ISOs bundled in 
#   My idea for this is to make the user enter the filepath manually, or if possible have a file explorer open for them to search for their ISOs and click on them to enter the filepath.)
#                   completed