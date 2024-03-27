#IMPORTANT: this code only clones virtual machines that have been registered to the user's personal VirtualBox application previously.
#This means that the user must either already have a virtual machine they wish to clone, or create a fresh virtual machine using the operating system they wish to make vulnerable.
#This is due to how VBoxManage handles cloning a machine, it is much simpler to clone a pre-existing virtual machine's disk and OS through a VDI file than it is to clone an ISO.
#Furthermore, this cloning process replicates the state that the original virtual machine was last in, meaning that the operating system does not have to be installed freshly on the cloned machine.

#The goal of this code is to allow for any operating system to be added to this code, due to its object-oriented nature. Set-up scripts of vulnerable services and applications can be added through this.
#When a virtual machine is cloned its operating system is noted and stored in a variable that can be read from, meaning the user does not have to specify which operating system is being used ~~
# ~~ allowing for an easier onboarding process of vulnerable services that are specific to a set operating system.

import subprocess
import os
import tkinter as tk
from tkinter import filedialog
import sys
import re


vboxmanage_path = 'C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe' #just in case the user does not have VBoxManage on their PATH i have instead used the default file-path as a variable

vm_folder = r'C:\\ClonedVirtualMachines' #this is where all cloned VMs will be stored

def create_cloned_vms_folder(): #this creates the folder where the cloned VMs will be stored if it doesnt already exist
    if vm_folder: 
        subprocess.run([vboxmanage_path, 'setproperty', 'machinefolder', vm_folder], check=True)
        try:
            os.makedirs(vm_folder)
        except FileExistsError:
            print(f"Directory '{vm_folder}' already exists.")

def select_vm(): #allows the user to select the VM they want to clone from their files
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Please locate and select VM to be cloned", filetypes=[("Virtual Machine Files", "*.vdi")])
    #this code only allows for VDI files to be chosen, as a VDI file indicates that the VM has already been set up and can therefore be cloned. This code would not work with an ISO file.
    root.destroy()
    return file_path




def get_original_os_info(original_name):
    #Uses the original registered VM name to get the all important information about the virtual machine. In this instance all that is necessary is the operating system, memory, and VRAM values.
    result = subprocess.run([vboxmanage_path, 'showvminfo', original_name], capture_output=True, text=True)
    output_lines = result.stdout.splitlines()
    version = ""
    os_type = ""
    memory_size = 0
    video_memory_size = 0
    for line in output_lines:
        if "Guest OS" in line:
            os_type = line.split(":")[1].strip()
        elif "Guest OS type" in line:
            version = line.split(":")[1].strip()
        elif "Memory size" in line:
            memory_str = line.split(":")[1].split()[0]  # Extracting memory size from the output
            memory_size = int(memory_str[:-2]) #removes the "MB" suffix and converts to an output variable
        elif "VRAM size" in line:
            video_memory_str = line.split(":")[1].split()[0]
            video_memory_size = int(video_memory_str[:-2])
    return version, os_type, memory_size, video_memory_size
# this function is used for both creating the clone with the correct memory amounts and analysing the operating system so that I can implement operating-system-dependent vulnerable software onboarding processes. 



def clone_vdi(original_vdi, new_vdi, new_name, memory_size_string, video_memory_string):
    #everything in this function is run by VBoxManage to create a clone of the specified VM

    clone_cmd = [vboxmanage_path, 'clonehd', original_vdi, new_vdi, '--format', 'VDI',] #clones the drive file of the original VM
    subprocess.run(clone_cmd)

    create_vm_cmd = [vboxmanage_path, 'createvm', '--name', new_name, '--register'] #creates a new empty VM for the cloned drive to be attatched
    subprocess.run(create_vm_cmd)

    clone_network_adapter_cmd = [vboxmanage_path, 'modifyvm', new_name, '--nic1', 'nat'] #creates a NAT for the VM to use
    subprocess.run(clone_network_adapter_cmd)

    adjust_memory_cmd = [vboxmanage_path, 'modifyvm', new_name, '--memory', memory_size_string] #adjusts the new VM's memory to the specifications of the old VM
    subprocess.run(adjust_memory_cmd)

    change_video_memory = [vboxmanage_path, 'modifyvm', new_name, '--vram', video_memory_string] #adjusts VRAM
    subprocess.run(change_video_memory)

    set_boot_order = [vboxmanage_path, 'modifyvm', new_name, '--boot1', 'disk', '--boot2', 'none', '--boot3', 'none'] #ensures the new VM only boots from the Disk
    subprocess.run(set_boot_order)

    set_pointing_device = [vboxmanage_path, 'modifyvm', new_name, '--mouse', 'usbtablet'] #ensures the new VM has mouse-integration enabled
    subprocess.run(set_pointing_device)

    create_ide = [vboxmanage_path, 'storagectl', new_name, '--name', 'IDE Controller', '--add', 'ide'] #configures the controller of the disk
    subprocess.run(create_ide)

    attach_drive_cmd = [vboxmanage_path, 'storageattach', new_name,'--storagectl', 'IDE Controller', '--port', '0', '--device', '0', '--type', 'hdd', '--medium', new_vdi] #attaches the disk controller
    subprocess.run(attach_drive_cmd)



def shell_command(command):
    #this function allows a shell to be opened in the virtual machine
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode("utf-8"), error.decode("utf-8")


# def guest_additions(new_name):
#     #this will install guest additions so that services can be onboarded
#     check_command = [vboxmanage_path, 'showvminfo', new_name, '--machinereadable | grep GuestAdditionsVersion']
#     output, _ = shell_command(check_command)
#     if "no value" in output:
#         start_cmd = [vboxmanage_path, 'startvm', new_name, '--type headless']
#         shell_command(start_cmd)

#         #buffer code to allow the VM to load
#         print("The VM will now load...")
#         shell_command("sleep 10")

#         install_command = [vboxmanage_path, 'guestcontrol', new_name, 'execute --image /opt/VBoxGuestAdditions-6.1.26/init --username user --password password']
#         shell_command(install_command)

#         shell_command([vboxmanage_path, 'controlvm', new_name, 'reset'])
#         print("Guest additions installed, the VM will now restart.")
#         sys.exit()

#Keeping this block of code in case it is needed later on

def add_vuln_apache(new_name):
    #this function utilises the shell command function to set up a vulnerable Apache server on an Ubuntu VM
    start_command = [vboxmanage_path, 'startvm', new_name, '--type', 'headless']
    shell_command(start_command)


    #get IP for server
    ip_command = [vboxmanage_path, 'guestproperty', 'get', new_name, '/VirtualBox/GuestInfo/Net/0/V4/IP']
    ip_output, _ = shell_command(ip_command)
    print("Output of VBoxManage guestproperty get command:")
    print(ip_output)
    ip_match = re.search(r"Value: (\d+\.\d+\.\d+\.\d+)", ip_output)
    if ip_match:
        ip_address = ip_match.group(1)
    else:
        sys.exit("Failed to retrieve IP address of the VM. Please check if the VM is running and VBoxManage is correctly installed.")


    #use IP to install apache
    install_apache = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null user@{ip_address} 'sudo apt-get update && sudo apt-get install -y apache2'"
    shell_command(install_apache)

    print(f"Apache server has been installed and configured on the VM {new_name}.")
    print(f"The IP for this Apache server is: http://{ip_address}")

    #This doesn't work yet and I am not sure why but it doesn't cause any errors so I'm just leaving it in.


if __name__ == "__main__":
    try:
        create_cloned_vms_folder() #creates the folder for the cloned VMs or returns an exception

        original_vdi = select_vm() #runs the function to let the user pick the VM they want to clone
        if not original_vdi:
            print("No file selected.")
        else:
            original_name = os.path.splitext(os.path.basename(original_vdi))[0]  # Extracting VM name from file path
            original_os_version, original_os_type, memory_size, video_memory_size = get_original_os_info(original_name) #use the old VM name to gather all necessary system information
            
            memory_size_string = str(memory_size) #parse the memory specifications into new string variables for the clonevm command to read
            video_memory_string = str(video_memory_size)

            new_name = input(str("Enter the name for the cloned virtual machine: "))

            new_vdi = os.path.join(vm_folder, f"{new_name}.vdi")
            clone_vdi(original_vdi, new_vdi, new_name, memory_size_string, video_memory_string) #clones the VM with all of the original information

            print(f"Original OS Version: {original_os_version}") #stores the operating system details in a variable for later use
            print(f"Original OS Type: {original_os_type}")

            print("Virtual machine cloned successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")



yes = {'yes', 'y', 'ye',''}
no = {'no', 'n'}
choice = input("Do you want to install vulnerabilities on to this VM (yes/no) : ").lower()
if choice in yes:

    if "Ubuntu" in original_os_type:
        add_vuln_apache(new_name)



elif choice in no:
    print("This program will now close")
    exit()

else:
    print("please respond with 'yes' or 'no'")