# tools/lab/xarch — ARM and RISC-V under qemu

qemu-user **wall time is not a performance measure**: it is dominated
by translating guest indirect branches, which a threaded interpreter
does on every dispatch. On AArch64 `loop`, CV8 runs 8% fewer
instructions than `relf-new` yet takes longer under qemu. What qemu
gives reliably, and what these scripts collect:

- correctness on real ARM/RISC-V instruction sets (`build.sh` smoke);
- exact guest instruction counts (`insns.sh`, qemu's `libinsn` plugin);
- a simulated L1 (`cache.sh`, qemu's `contrib/plugins/cache.c`).

Branch prediction is not modelled by anything here.

## One-time setup (Ubuntu 24.04)

    apt-get install qemu-user gcc-aarch64-linux-gnu \
        gcc-arm-linux-gnueabihf gcc-riscv64-linux-gnu \
        ninja-build libglib2.0-dev pkg-config python3-venv flex bison
    # Ubuntu's qemu has no plugin support; build 8.2.2 with it:
    git clone --depth 1 --branch v8.2.2 https://github.com/qemu/qemu.git
    cd qemu && sed -i "s/^\(\s*\)subdir('fp')/\1# &/" tests/meson.build
    mkdir build && cd build
    ../configure --target-list=aarch64-linux-user,arm-linux-user,riscv64-linux-user \
        --enable-plugins --disable-system --disable-docs --disable-tools \
        --disable-werror --disable-capstone --disable-slirp --disable-fdt
    ninja qemu-aarch64 qemu-arm qemu-riscv64 tests/plugin/libinsn.so
    cd ../contrib/plugins && gcc -O2 -shared -fPIC -I../../include/qemu \
        $(pkg-config --cflags glib-2.0) cache.c -o ../../build/libcache.so \
        $(pkg-config --libs glib-2.0)

(The `tests/fp` edit skips qemu's own float tests, whose subproject is
fetched from gitlab.)

## Use

    bash tools/lab/build-cv8.sh /tmp/cv8b            # images (+ x86 engines)
    QEMU=/path/to/qemu/build bash tools/lab/xarch/build.sh /tmp/cv8b /tmp/xa
    QEMU=... bash tools/lab/xarch/insns.sh /tmp/cv8b /tmp/xa > insns.txt
    QEMU=... bash tools/lab/xarch/cache.sh /tmp/cv8b /tmp/xa > cache.txt
    python3 tools/lab/xarch/analyse.py insns.txt

Images are built once, on any host: the same-width image runs on
every architecture unchanged (checked on all three).
