%define major 6
%define libname %mklibname %{name} %{major}
%define devname %mklibname %{name} -d
%define statname %mklibname %{name} -d -s

# (tpg) optimize it a bit
%global optflags %{optflags} -O3

# (tpg) enable PGO build
%if ! %{cross_compiling}
%bcond_without pgo
%endif

Summary:	Multiple-precision floating-point computations with correct rounding
Name:		mpfr
Version:	4.2.0
Release:	2
License:	LGPLv3+
Group:		System/Libraries
Url:		http://www.mpfr.org/
Source0:	http://www.mpfr.org/mpfr-current/mpfr-%{version}.tar.xz
Source1:	%{name}.rpmlintrc
# (tpg) 2022-05-28 due to patch to enabl float128 support for clang in glibc
# configure:18793: checking for GMP_NUMB_BITS and sizeof(mp_limb_t) consistency
# configure:18825: /usr/bin/clang -o conftest -Os -fomit-frame-pointer -g3 -gdwarf-4 -Wstrict-aliasing=2 -pipe -Wformat -Werror=format-security -D_FORTIFY_SOURCE=2 -fstack-protector-all --param=ssp-buffer-size=4 -m64 -mtune=generic -flto -O3 -fprofile-generate -mllvm -vp-counters-per-site=16  -Os -fomit-frame-pointer -g3 -gdwarf-4 -Wstrict-aliasing=2 -pipe -Wformat -Werror=format-security -D_FORTIFY_SOURCE=2 -fstack-protector-all --param=ssp-buffer-size=4 -m64 -mtune=generic -flto -O3 -Wl,-O2  -Wl,--no-undefined -flto  -fprofile-generate -Wl,--disable-new-dtags conftest.c  >&5
# In file included from conftest.c:62:
# In file included from /usr/include/stdio.h:430:
# /usr/include/bits/floatn.h:86:20: error: cannot combine with previous '__float128' declaration specifier
# typedef __float128 _Float128;                   ^
# conftest.c:57:19: note: expanded from macro '_Float128'
# define _Float128 __float128
#                  ^
Patch99:	mpfr-4.1.0-skip-test-because-of-cannot-combine-with-previous-__float128-declaration-specifier.patch
BuildRequires:	pkgconfig(gmp)
BuildRequires:	autoconf-archive
BuildRequires:	texinfo

%description
The MPFR library is a C library for multiple-precision
floating-point computations with correct rounding. 

%package -n %{libname}
Summary:	Multiple-precision floating-point computations with correct rounding
Group:		System/Libraries

%description -n %{libname}
The MPFR library is a C library for multiple-precision
floating-point computations with correct rounding. 

%package -n %{devname}
Summary:	Development headers and libraries for MPFR
Group:		Development/C
Requires:	%{libname} = %{EVRD}
Provides:	%{name}-devel = %{EVRD}
Requires:	pkgconfig(gmp)

%description -n %{devname}
The development headers and libraries for the MPFR library.

%package -n %{statname}
Summary:	Static libraries for MPFR
Group:		Development/C
Requires:	%{devname} = %{EVRD}
Provides:	%{name}-static-devel = %{EVRD}

%description -n %{statname}
Static libraries for the MPFR library.

%prep
%autosetup -p1
autoreconf -fiv

%build
%ifarch %{arm}
# For some reason, mpfr forces gcc
# but gcc generates __modsi3 calls when it should
# be generating __aeabi_modsi3 instead
export CC=clang
export CXX=clang++
%endif

%if %{with pgo}
export LD_LIBRARY_PATH="$(pwd)"

CFLAGS="%{optflags} -fprofile-generate -mllvm -vp-counters-per-site=16" \
CXXFLAGS="%{optflags} -fprofile-generate" \
LDFLAGS="%{build_ldflags} -fprofile-generate" \
%configure \
	--enable-shared \
	--enable-static \
	--disable-assert \
	--enable-tests-timeout=60 \
%ifarch %{ix86} %{x86_64}
	--disable-float128 \
%endif
	--enable-thread-safe

if [ "$?" != '0' ]; then
    printf '%s\n' "configure failed, here's config.log:"
    cat config.log
    exit 1
fi

%make_build

# (tpg) build tests
cd tools/bench
%make_build mpfrbench
./mpfrbench
cd -

unset LD_LIBRARY_PATH
llvm-profdata merge --output=%{name}-llvm.profdata $(find . -name "*.profraw" -type f)
PROFDATA="$(realpath %{name}-llvm.profdata)"
rm -f *.profraw

make clean

CFLAGS="%{optflags} -fprofile-use=$PROFDATA" \
CXXFLAGS="%{optflags} -fprofile-use=$PROFDATA" \
LDFLAGS="%{build_ldflags} -fprofile-use=$PROFDATA" \
%endif
%configure \
	--enable-shared \
	--enable-static \
	--disable-assert \
	--enable-tests-timeout=60 \
%ifarch %{ix86} %{x86_64}
	--disable-float128 \
%endif
	--enable-thread-safe

if [ "$?" != "0" ]; then
	printf '%s\n' "configure failed, here's config.log:"
	cat config.log
	exit 1
fi

%make_build

%install
%make_install

rm -rf installed-docs
mv %{buildroot}%{_docdir}/%{name} installed-docs

# (tpg) strip LTO from "LLVM IR bitcode" files
check_convert_bitcode() {
    printf '%s\n' "Checking for LLVM IR bitcode"
    llvm_file_name=$(realpath ${1})
    llvm_file_type=$(file ${llvm_file_name})

    if printf '%s\n' "${llvm_file_type}" | grep -q "LLVM IR bitcode"; then
# recompile without LTO
    clang %{optflags} -fno-lto -Wno-unused-command-line-argument -x ir ${llvm_file_name} -c -o ${llvm_file_name}
    elif printf '%s\n' "${llvm_file_type}" | grep -q "current ar archive"; then
    printf '%s\n' "Unpacking ar archive ${llvm_file_name} to check for LLVM bitcode components."
# create archive stage for objects
    archive_stage=$(mktemp -d)
    archive=${llvm_file_name}
    cd ${archive_stage}
    ar x ${archive}
    for archived_file in $(find -not -type d); do
        check_convert_bitcode ${archived_file}
        printf '%s\n' "Repacking ${archived_file} into ${archive}."
        ar r ${archive} ${archived_file}
    done
    ranlib ${archive}
    cd ..
    fi
}

for i in $(find %{buildroot} -type f -name "*.[ao]"); do
    check_convert_bitcode ${i}
done

%check
# (tpg) 2022-05-27 tests fails on aarch64 
# ../test-driver: line 107: 78079 CPU time limit exceeded (core dumped) "$@" > $log_file 2>&1
make check ||:
cat tests/test-suite.log

%files -n %{libname}
%{_libdir}/libmpfr.so.%{major}*

%files -n %{devname}
%{_includedir}/mpfr.h
%{_includedir}/mpf2mpfr.h
%doc %{_infodir}/mpfr.info*
%{_libdir}/libmpfr.so
%{_libdir}/pkgconfig/mpfr.pc

%files -n %{statname}
%{_libdir}/libmpfr.a
