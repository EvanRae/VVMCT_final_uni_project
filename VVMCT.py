#The Vulnerable Virtual Machine Creation Tool (VVMCT)


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
import time


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Functions and variable definition~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

vboxmanage_path = 'C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe' #just in case the user does not have VBoxManage on their PATH i have instead used the default file-path as a variable

guest_additions_path = 'C:\\Program Files\\Oracle\\VirtualBox\\VBoxGuestAdditions.iso'

vm_folder = r'C:\\ClonedVirtualMachines' #this is where all cloned VMs will be stored

ip_address = "192.168.1.100" 
netmask = "255.255.255.0"  
gateway = "192.168.1.1"
#necessary info for setting up services (sometimes the cloned VMs would fail to create their own IPs and gateways, this circumvents the issue)

def create_cloned_vms_folder(): #this creates the folder where the cloned VMs will be stored if it doesnt already exist
    if vm_folder: 
        subprocess.run([vboxmanage_path, 'setproperty', 'machinefolder', vm_folder], check=True)
        try:
            os.makedirs(vm_folder)
            print(f"Directory '{vm_folder}' was created")
        except FileExistsError:
            return

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

    clone_cmd = [vboxmanage_path, 'clonehd', original_vdi, new_vdi, '--format', 'VDI',] 
    #clones the drive file of the original VM
    subprocess.run(clone_cmd)

    create_vm_cmd = [vboxmanage_path, 'createvm', '--name', new_name, '--register'] 
    #creates a new empty VM for the cloned drive to be attatched
    subprocess.run(create_vm_cmd)

    clone_network_adapter_cmd = [vboxmanage_path, 'modifyvm', new_name, '--nic1', 'nat'] 
    #creates a NAT for the VM to use
    subprocess.run(clone_network_adapter_cmd)

    adjust_memory_cmd = [vboxmanage_path, 'modifyvm', new_name, '--memory', memory_size_string] 
    #adjusts the new VM's memory to the specifications of the old VM
    subprocess.run(adjust_memory_cmd)

    change_video_memory = [vboxmanage_path, 'modifyvm', new_name, '--vram', video_memory_string] 
    #adjusts VRAM
    subprocess.run(change_video_memory)

    set_boot_order = [vboxmanage_path, 'modifyvm', new_name, '--boot1', 'disk', '--boot2', 'none', '--boot3', 'none'] 
    #ensures the new VM only boots from the Disk
    subprocess.run(set_boot_order)

    set_pointing_device = [vboxmanage_path, 'modifyvm', new_name, '--mouse', 'usbtablet'] 
    #ensures the new VM has mouse-integration enabled
    subprocess.run(set_pointing_device)

    create_ide = [vboxmanage_path, 'storagectl', new_name, '--name', 'IDE Controller', '--add', 'ide'] 
    #configures the controller of the disk
    subprocess.run(create_ide)

    attach_drive_cmd = [vboxmanage_path, 'storageattach', new_name,'--storagectl', 'IDE Controller', '--port', '0', '--device', '0', '--type', 'hdd', '--medium', new_vdi] 
    #attaches the disk controller
    subprocess.run(attach_drive_cmd)

    add_guest_additions = [vboxmanage_path, 'storageattach', new_name, '--storagectl', 'IDE Controller', '--port', '1', '--device', '0', '--type', 'dvddrive', '--medium', guest_additions_path]
    #installs guest additions to the VM (This only works if the original VM has guest additions already enabled, this is just a carry-over empty dvd drive)
    subprocess.run(add_guest_additions)

    change_graphics_controller = [vboxmanage_path, 'modifyvm', new_name, '--graphicscontroller', 'vmsvga'] 
    #changes the graphics controller from the default VboxVGA to VMSVGA as it is more stable and works more often
    subprocess.run(change_graphics_controller)


def start_vm(new_name): #self explanitory
    try:
        start = [vboxmanage_path, 'startvm', new_name]
        subprocess.run(start)
        print("The VM is starting...")
    except:
        print(f"Error: {e}")


def shell_command(command):
    try:
    #this function allows a shell to be opened in the virtual machine
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        return output.decode("utf-8"), error.decode("utf-8")
    
    except:
        return None, str(e)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Ubuntu Vuln Scripts~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def add_vuln_apache(new_name):
    print("Initialising Apache install script")

    # Wait for VM to load
    print("Waiting for the virtual machine to start...")
    time.sleep(25)

    apache_command = ['sudo apt-get update && sudo apt-get install -y apache2']


    print("Installing Apache2")
    add_apache = [vboxmanage_path, 'guestcontrol', new_name, 'run','--username', 'username', '--password', 'password', '--', '/bin/bash', '-c', ' '.join(apache_command) ]
    output, error = shell_command(add_apache) 

    if error:
        print(f"Apache installed sucessfully, the Apache server can be found at the default local host 127.0.0.1")
    else:
        print(f"Failed to install Apache: {error}")
    
    #this final if/else statement for some reason would print an error even though the install was successful. I have flipped the conditions around to mitigate this.


def add_vuln_mySQL(new_name, mySQLRun):
    #adding a vulnerable mySQL server
    subprocess.run([vboxmanage_path, 'controlvm', new_name, 'reset'], check=True, bufsize=0)
    print("Initialising MySQL install script")
    print("The VM will now restart...")
    print("Waiting for the virtual machine to start...")
    time.sleep(25)

    

    print("adding MySQL to the VM...")


    install_script = ['echo "mysql-server mysql-server/root_password password root" | sudo debconf-set-selections && echo "mysql-server mysql-server/root_password_again password root" | sudo debconf-set-selections && sudo apt-get -y install mysql-server']
    #this install script anticipates the requests for a password and sets it as "root" before running the command to install MySQL
    mySQLInstall = [vboxmanage_path, 'guestcontrol', new_name, 'run','--username', 'username', '--password', 'password', '/bin/bash', '--', '-c', ' '.join(install_script)]
    subprocess.run(mySQLInstall)
    print("MySQL Successfully Installed")

    #this took 14 different code attempts, and a week and a half to get running. All of that for the code to end up being one really long sudo script. my sanity dwindles by the day.
    #and this is literally just so that i could go to the next vulnerability: installing wordpress
    #i have 3 weeks left to finish this...

    mySQLRun == True
    return mySQLRun


def add_wordpress(new_name, mySQLRun):
    
    subprocess.run([vboxmanage_path, 'controlvm', new_name, 'reset'], check=True, bufsize=0)
    print("Initialising Wordpress install script")
    print("The VM will now restart...")
    print("Waiting for the virtual machine to start...")
    time.sleep(25)
    
    print("Installing Wordpress...")
    wordpress_command = ['sudo wget https://wordpress.org/latest.tar.gz && tar -xzf latest.tar.gz -C /var/www/html/ && sudo chown -R www-data:www-data /var/www/html/wordpress && sudo chmod -R 755 /var/www/html/wordpress/ && sudo mv /var/www/html/wordpress/wp-config-sample.php /var/www/html/wordpress/wp-config.php']
    wordpressInstall = [vboxmanage_path, 'guestcontrol', new_name, 'run','--username', 'username', '--password', 'password', '/bin/bash', '--', '-c', ' '.join(wordpress_command)]
    subprocess.run(wordpressInstall)

    

    sys.exit()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Windows Vuln Scripts~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def JRE_install(new_name):
   
    print("Waiting for the VM to turn on...")
    time.sleep(80)

    print("Adding Java Runtime Environment...")



    host_file = 'C:\\VVMCT_dependencies\\JRE_x64.exe' #the dependencies folder must be in this location
    vm_destination = '/Users/Username/Desktop/JRE_64.exe'
    
    copy_command = [vboxmanage_path, 'guestcontrol', new_name, 'copyto', host_file, vm_destination, '--username', 'Username', '--password', 'password'] 
    #copies from Host to VM without needing a shared folder
    subprocess.run(copy_command)
    print("Java Runtime Environment Sucessfully added.")
    
    time.sleep(5)
    run_JRE = [vboxmanage_path, 'guestcontrol', new_name, 'start', vm_destination, '--username', 'Username', '--password', 'password']
    subprocess.run(run_JRE)
    #this final section will only run if the program is started as administrator


def acrobat_install(new_name):
    # print("Waiting for the VM to turn on...")
    # time.sleep(80)

    print("Adding Adobe Acrobat Reader...")

    host_file = 'C:\\VVMCT_dependencies\\AcrobatReader.exe'
    vm_destination = '/Users/Username/Desktop/AcrobatReader.exe'

    copy_command = [vboxmanage_path, 'guestcontrol', new_name, 'copyto', host_file, vm_destination, '--username', 'Username', '--password', 'password']
    #copies from Host to VM without needing a shared folder
    subprocess.run(copy_command)
    print("Adobe Acrobat Reader Sucessfully added.")

    time.sleep(15)
    run_AAR = [vboxmanage_path, 'guestcontrol', new_name, 'start', vm_destination, '--username', 'Username', '--password', 'password']
    subprocess.run(run_AAR)
    #this final section will only run if the program is started as administrator.

    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ADD VULNERABILITIES~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def add_vulns(new_name, original_os_type, original_os_version):
    yes = {'yes', 'y', 'ye',''}
    no = {'no', 'n'}
    choice = input("Do you want to install vulnerabilities on to this VM (yes/no) : ").lower()
    if choice in yes:

        if "Ubuntu" in original_os_type:

            start_vm(new_name)
            add_vuln_apache(new_name)
            add_vuln_mySQL(new_name)
            add_wordpress(new_name)
    
        if "Windows 10" in original_os_type:
            start_vm(new_name)
            JRE_install(new_name)
            acrobat_install(new_name)

    


    elif choice in no:
        print("This program will now close")
        exit()

    else:
        print("please respond with 'yes' or 'no'")
        add_vulns(new_name, original_os_type, original_os_version)



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~operating code~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

print("""
                                    Welcome to the Vulnerable Virtual Machine Creation Tool (VVMCT).")
      
The VVMCT operates based on the default location of VirtualBox, please install VirtualBox in its default location if you have not done so already.
        Please ensure that any VM that you wish to clone has been properly installed and registered to your machine's VirtualBox client.
Please also ensure that Sudo commands are permitted guest additions have been pre-installed on to the VM you wish to add vulnerabilities to.
        A guide for guest additions can be found here: https://bjordanov.com/install-guest-additions-virtual-machine-vm-virtualbox/
      
                                                    Select the VM you wish to clone""")


if __name__ == "__main__":
    try:
        create_cloned_vms_folder() #creates the folder for the cloned VMs or returns an exception

        original_vdi = select_vm() #runs the function to let the user pick the VM they want to clone
        if not original_vdi:
            print("No file selected.")
            sys.exit()
        else:
            original_name = os.path.splitext(os.path.basename(original_vdi))[0]  # Extracting VM name from file path
            original_os_version, original_os_type, memory_size, video_memory_size = get_original_os_info(original_name) #use the old VM name to gather all necessary system information
            
            memory_size_string = str(memory_size) #parse the memory specifications into new string variables for the clonevm command to read
            video_memory_string = str(video_memory_size)

            new_name = input(str("Enter the name for the cloned virtual machine: "))

            new_vdi = os.path.join(vm_folder, f"{new_name}.vdi")
            clone_vdi(original_vdi, new_vdi, new_name, memory_size_string, video_memory_string) #clones the VM with all of the original information

            if "Fedora" in original_os_type:
                acpi_off = [vboxmanage_path, 'modifyvm', new_name, '--acpi', 'off']
                subprocess.run(acpi_off)
                ioapic_off = [vboxmanage_path, 'modifyvm', new_name, '--ioapic', 'off']
                subprocess.run(ioapic_off)
                #i'll be honest and say I don't know exactly what these lines of code do, but Fedora VMs won't load without them so they're staying here
                #However these lines of code cause Windows VMs to blue screen so I had to make a seperate statement to load these for just Fedora OSs


            print(f"Original OS Version: {original_os_version}") #stores the operating system details in a variable for later use
            print(f"Original OS Type: {original_os_type}")

            print("Virtual machine cloned successfully!")
            add_vulns(new_name, original_os_type, original_os_version)
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure that the VM you are trying to clone is registered to your VirtualBox client (installing and running a VM will register it)")






















#old or not working code dump (may still be useful)


# def add_vuln_apache(new_name):
#     #this function utilises the shell command function to set up a vulnerable Apache server on an Ubuntu VM

#     guest_additions(new_name)

#     start_command = [vboxmanage_path, 'startvm', new_name, '--type', 'headless']
#     shell_command(start_command)

#     # Wait for VM to restart
#     print("Waiting for the virtual machine to restart...")
#     time.sleep(20)

#     #get IP for server
#     ip_command = [vboxmanage_path, 'guestproperty', 'enumerate', new_name]
#     ip_output, _ = shell_command(ip_command)
#     print("Output of VBoxManage guestproperty get command:")
#     print(ip_output)
#     ip_match = re.search(r"/VirtualBox/GuestInfo/Net/\d+/V4/IP, value: (\d+\.\d+\.\d+\.\d+)", ip_output)
#     if ip_match:
#         ip_address = ip_match.group(1)
#     else:
#         sys.exit("Failed to retrieve IP address of the VM. Please check if the VM is running and VBoxManage is correctly installed.")


#     #use IP to install apache
#     install_apache = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null user@{ip_address} 'sudo apt-get update && sudo apt-get install -y apache2'"
#     shell_command(install_apache)

#     print(f"Apache server has been installed and configured on the VM {new_name}.")
#     print(f"The IP for this Apache server is: http://{ip_address}")

#     #This doesn't work and I am not sure why but it doesn't cause any errors so I'm just leaving it in.




#def guest_additions(new_name):
#      #this will install guest additions so that services can be onboarded
#      #check_command = [vboxmanage_path, 'showvminfo', new_name, '--machinereadable | grep GuestAdditionsVersion']
#     # output, _ = shell_command(check_command)
#     # if "no value" in output:
#          #start_cmd = [vboxmanage_path, 'startvm', new_name, '--type headless']
#          #shell_command(start_cmd)

#          #buffer code to allow the VM to load
#     print("The VM will now load...")
#     time.sleep(30)

#     #add_additions = [vboxmanage_path, 'controlvm', new_name, 'guestcontrol', 'service', 'install', 'VBoxGuestAdditions', '--verbose']
#     #subprocess.run(add_additions)
#     #print("Guest additions installed")
#     install_command = [vboxmanage_path, 'guestcontrol', new_name, 'execute --image /opt/VBoxGuestAdditions-6.1.26/init --username user --password password'] #loads guest additions on to the VM
#     subprocess.run(install_command)

#     #shell_command([vboxmanage_path, 'controlvm', new_name, 'reset'])
#     #print("Guest additions installed, the VM will now restart.")


# def add_static_ip(new_name, ip_address, netmask, gateway):
#     set_ip = [vboxmanage_path, 'guestproperty', 'set', new_name, '/VirtualBox/GuestInfo/Net/0/V4/IP', ip_address] #set the IP address of the new machine
#     subprocess.run(set_ip)
#     set_netmask = [vboxmanage_path, 'guestproperty', 'set', new_name, '/VirtualBox/GuestInfo/Net/0/V4/Netmask', netmask] #set the netmask
#     subprocess.run(set_netmask)
#     set_gateway = [vboxmanage_path, 'guestproperty', 'set', new_name, '/VirtualBox/GuestInfo/Net/0/V4/Gateway', gateway] #set the default gateway
#     subprocess.run(set_gateway)


    # host_path = r'C:\\VVMCT_dependencies'
    # folder_name = 'shared_folder'
    # guest_drive_letter = 'C:'

    # try:
    #     # subprocess.run([vboxmanage_path, 'sharedfolder', 'add', new_name, '--name', folder_name, '--hostpath', host_path, '--automount']) #creates a shared folder between the VM and the host
    #     mount_command = [f'VBoxManage guestcontrol "{new_name}" --username "Username" --password "password" run --exe "cmd.exe" -- "net use {guest_drive_letter} \\\\vboxsvr\\{folder_name}"']
    #     subprocess.run(mount_command)
    #     print(mount_command)
    #     install_command = f'{guest_drive_letter}\\{folder_name}\\JRE_64.exe'
    #     subprocess.run(install_command)
    # except subprocess.CalledProcessError as e:
    #         if "VBOX_E_INVALID_OBJECT_STATE" in str(e):
    #             print("Virtual machine is already in use or locked. Retrying in 10 seconds...")
    #             time.sleep(10)
    #             JRE_install(new_name)


    # JRE_path = r'C:\\VVMCT_dependencies\\JRE_64.exe' #path to the java runtime extension installer
    # print("Waiting for the VM to turn on...")
    # time.sleep(80)

    # print("Installing Java Runtime Environment...")
    # install_command = [vboxmanage_path, 'guestcontrol', new_name, 'run', '--exe', JRE_path, '--username', 'Username', '--password', 'password', '--wait-stdout']
    # output, error = shell_command(install_command)

    # print(error)

    # if error:
    #     print(f"Error occurred: {error}")
    # else:
    #     print("Java Runtime Extension successfully installed.")

    # subprocess.run([vboxmanage_path, 'guestcontrol', new_name, 'run', '--exe', JRE_path], bufsize=1)

    #both of these versions of the command don't seem to work.
