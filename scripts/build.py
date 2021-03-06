#!/usr/bin/env python3
import argparse
import subprocess
import os
import shutil


def main():
    uefi_compiler_name = "$HOME/opt/LanternOS-toolchain/bin/x86_64-w64-mingw32-gcc"
    kernel_compiler_name = "$HOME/opt/LanternOS-toolchain/bin/x86_64-elf-gcc"
    build_type = "Release"
    run_tests = "OFF"
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ueficompiler", help="Specify the full path to where you installed the uefi cross-compiler."
        " This is only needed if you installed the toolchain to a nondefault directory.")
    parser.add_argument(
        "--kernelcompiler", help="Specify the full path to where you installed the elf cross-compiler."
        " This is only needed if you installed the toolchain to a nondefault directory.")
    parser.add_argument("--build", help="Whether to build Debug or Release. Default is release.")
    parser.add_argument("--tests", action='store_true', help="Whether you wish to build and run unit tests.")
    parser.add_argument("Mingw_Header_Dir",
                        help="Provide the full path to your installation of the mingw headers.")
    args = parser.parse_args()

    mingw_header_dir = args.Mingw_Header_Dir

    if args.ueficompiler:
        uefi_compiler_name = args.ueficompiler
    if args.kernelcompiler:
        kernel_compiler_name = args.kernelcompiler
    if args.build:
        build_type = args.build
    if args.tests:
        run_tests = "ON"

    uefi_compiler_name = os.path.expandvars(uefi_compiler_name)
    kernel_compiler_name = os.path.expandvars(kernel_compiler_name)

    # build EFI bootloader
    os.chdir("../bhavaloader")
    subprocess.run(["cmake", "-S.", "-B../build/{}/bhavaloader".format(build_type),
                   "-DCMAKE_CXX_COMPILER={}".format(uefi_compiler_name),
                    "-DCMAKE_BUILD_TYPE={}".format(build_type),
                    "-DMINGW_HEADERS_DIR={}".format(mingw_header_dir)])
    subprocess.run(["make", "-C../build/{}/bhavaloader".format(build_type)])
    os.chdir("../scripts")

    # TODO: Build libk
    os.chdir("../namelesslibc/libk/")
    subprocess.run(["cmake", "-S.", "-B../build/{}/namelesslibc".format(build_type),
                   "-DCMAKE_CXX_COMPILER={}".format(kernel_compiler_name),
                    "-DCMAKE_BUILD_TYPE={}".format(build_type),
                    "-DBUILD_TESTS={}".format(run_tests)])
    subprocess.run(["make", "-C../build/{}/namelesslibc".format(build_type)])
    os.chdir("../../scripts")

    # TODO: Build kernel
    os.chdir("../lanternOS/kernel/")
    subprocess.run(["cmake", "-S.", "-B../../build/{}/kernel".format(build_type),
                    "-DCMAKE_CXX_COMPILER={}".format(kernel_compiler_name),
                   "-DCMAKE_BUILD_TYPE={}".format(build_type)])
    subprocess.run(["make", "-C../../build/{}/kernel".format(build_type)])
    os.chdir("../../scripts")

    os.chdir("../build/{}/kernel/bin/".format(build_type))
    subprocess.run(["objcopy", "--only-keep-debug", "LanternOS", "LanternOS.dbg"])
    subprocess.run(["objcopy", "--strip-debug", "LanternOS"])
    os.chdir("../../../../scripts")

    if (build_type == "Debug"):
        os.replace("../build/Release/kernel/bin/LanternOS.dbg", "../VMTestBed/Boot/LanternOS.dbg")

    os.makedirs("../VMTestBed/Boot/EFI/Boot/", exist_ok=True)
    os.replace("../build/{}/bhavaloader/bin/BhavaLoader.exe".format(build_type),
               "../VMTestBed/Boot/EFI/Boot/Bootx64.efi")
    os.replace("../build/{}/kernel/bin/LanternOS".format(build_type), "../VMTestBed/Boot/LanternOS")

    shutil.copyfile("../Vendor/font/font.psf", "../VMTestBed/Boot/font.psf")

    os.environ["LD_PRELOAD"] = "{}/../namelesslibc/build/Release/namelesslibc/bin/libnamelesslibkfortesting.so".format(
        os.getcwd())
    if (run_tests == "ON"):
        print("================================")
        print("========= UNIT TESTS ===========")
        print("================================")
        print("Begin running tests for libk...")
        os.chdir("../namelesslibc/build/{}/namelesslibc/bin/".format(build_type))
        subprocess.run(['./namelesslibk_tests'])
        os.chdir("../../../../../scripts")


if __name__ == "__main__":
    main()
