%define major 6
%define libname %mklibname %{name} %{major}
%define devname %mklibname %{name} -d
%define statname %mklibname %{name} -d -s
%bcond_with crosscompile

# (tpg) configure script is broken when LTO is used
# so disable it and push LTO at make_build stage
%define _disable_lto 1

# (tpg) optimize it a bit
%global optflags %optflags -O3

# (tpg) enable PGO build
%ifnarch aarch64
%bcond_with pgo
%else
%bcond_with pgo
%endif

Summary:	Multiple-precision floating-point computations with correct rounding
Name:		mpfr
Version:	4.1.0
Release:	5
License:	LGPLv3+
Group:		System/Libraries
Url:		http://www.mpfr.org/
Source0:	http://www.mpfr.org/mpfr-current/mpfr-%{version}.tar.xz
Source1:	%{name}.rpmlintrc
Patch0:		https://www.mpfr.org/mpfr-current/patch01
Patch1:		https://www.mpfr.org/mpfr-current/patch02
Patch2:		https://www.mpfr.org/mpfr-current/patch03
Patch3:		https://www.mpfr.org/mpfr-current/patch04
Patch4:		https://www.mpfr.org/mpfr-current/patch05
Patch5:		https://www.mpfr.org/mpfr-current/patch06
Patch6:		https://www.mpfr.org/mpfr-current/patch07
Patch7:		https://www.mpfr.org/mpfr-current/patch08
Patch8:		https://www.mpfr.org/mpfr-current/patch09
Patch9:		https://www.mpfr.org/mpfr-current/patch10
Patch10:	https://www.mpfr.org/mpfr-current/patch11
Patch11:	https://www.mpfr.org/mpfr-current/patch12
Patch12:	https://www.mpfr.org/mpfr-current/patch13
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

%build
%ifarch %{arm}
# For some reason, mpfr forces gcc
# but gcc generates __modsi3 calls when it should
# be generating __aeabi_modsi3 instead
export CC=clang
export CXX=clang++
%endif

%if %{with pgo}
export LLVM_PROFILE_FILE=%{name}-%p.profile.d
export LD_LIBRARY_PATH="$(pwd)"
CFLAGS="%{optflags} -fprofile-instr-generate" \
CXXFLAGS="%{optflags} -fprofile-instr-generate" \
FFLAGS="$CFLAGS_PGO" \
FCFLAGS="$CFLAGS_PGO" \
LDFLAGS="%{ldflags} -fprofile-instr-generate" \
%configure \
	--enable-shared \
	--enable-static \
%ifarch %{ix86} %{x86_64}
	--disable-float128 \
%endif
%if %{with crosscompile}
	--with-gmp-lib=%{_prefix}/%{_target_platform}/sys-root%{_libdir} \
%endif
	--enable-thread-safe

if [ "$?" != '0' ]; then
    echo "configure failed, here's config.log:"
    cat config.log
    exit 1
fi

# (tpg) configure script is sensitive on LTO so disable it and re-enable on make stage
# 2020-07-13 disable LTO on riscv
%ifnarch %{riscv}
%make_build CFLAGS="%{optflags} -flto" CXXFLAGS="%{optflags} -flto" LDFLAGS="%{ldflags} -flto"
%else
%make_build
%endif

export LD_LIBRARY_PATH="%{buildroot}%{_libdir}"
make check
cat tests/test-suite.log

cd tools/bench
make bench
cd -
unset LD_LIBRARY_PATH
unset LLVM_PROFILE_FILE
llvm-profdata merge --output=%{name}.profile *.profile.d

make clean

CFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
CXXFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
LDFLAGS="%{ldflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
%endif

%ifarch %{aarch64}
# FIXME workaround for "make test" failure that also
# results in hangs while building libstdc++
# If you remove this, make sure "make test" succeeds
# and is reasonably fast, and that gcc builds successfully.
# (tpg) 2021-11-09 tests still fails, so keep gcc on aarch64
export CC=gcc
export CXX=g++
%endif

%configure \
	--enable-shared \
	--enable-static \
%ifarch %{ix86} %{x86_64}
	--disable-float128 \
%endif
%if %{with crosscompile}
	--with-gmp-lib=%{_prefix}/%{_target_platform}/sys-root%{_libdir} \
%endif
	--enable-thread-safe

if [ "$?" != "0" ]; then
	printf '%s\n' "configure failed, here's config.log:"
	cat config.log
	exit 1
fi

# (tpg) configure script is sensitive on LTO so disable it and re-enable on make stage
# 2020-07-13 disable LTO on riscv
%ifnarch %{riscv}
%make_build CFLAGS="%{optflags} -flto" CXXFLAGS="%{optflags} -flto" LDFLAGS="%{ldflags} -flto"
%else
%make_build
%endif

%install
%make_install

rm -rf installed-docs
mv %{buildroot}%{_docdir}/%{name} installed-docs

%check
make check
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
