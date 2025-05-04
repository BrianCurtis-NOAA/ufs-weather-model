import machine
import subprocess

def generate_log():
    machineID = machine.detect_machine()
    logFile=f"RegressionTests_{machineID}.log"
    print(f"Log File: {logFile}")
    lfopen = open(logFile, "w")

    lfopen.write(f"====START OF {machineID.upper()} REGRESSION TESTING LOG====\n\n"\
                 "UFSWM Hash:")
    git_hash, submodule_hashes=git_hashes()
    print(git_hash.stdout.decode('UTF-8'), file=lfopen)

    lfopen.write("Submodules:\n")
    print(submodule_hashes.stdout.decode("UTF-8"), file=lfopen)

def git_hashes():
    git_hash=subprocess.run("git rev-parse HEAD", shell=True, check=True, capture_output=True)
    submodule_hashes=subprocess.run("git submodule status --recursive", shell=True, check=True, capture_output=True)

    return git_hash, submodule_hashes

if __name__ == "__main__":
    generate_log()