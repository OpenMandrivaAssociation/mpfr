%define major 6
%define libname %mklibname %{name} %{major}
%define devname %mklibname %{name} -d
%define statname %mklibname %{name} -d -s
%bcond_with crosscompile

# (tpg) optimize it a bit
%global optflags %optflags -O3

# (tpg) enable PGO build
%bcond_without pgo

Summary:	Multiple-precision floating-point computations with correct rounding
Name:		mpfr
Version:	4.0.2
Release:	4
License:	LGPLv3+
Group:		System/Libraries
Url:		http://www.mpfr.org/
Source0:	http://www.mpfr.org/mpfr-current/mpfr-%{version}.tar.xz
Source1:	%{name}.rpmlintrc
Patch0:		https://www.mpfr.org/mpfr-4.0.2/patch01
Patch1:		floating-point-format-no-lto.patch
BuildRequires:	gmp-devel
BuildRequires:	autoconf-archive

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
%ifarch %{ix86}
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

%make_build
make check
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
%configure \
	--enable-shared \
	--enable-static \
%ifarch %{ix86}
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

%make_build

%install
%make_install

rm -rf installed-docs
mv %{buildroot}%{_docdir}/%{name} installed-docs

%check
# FIXME tset_float128 is known to fail on ix86
%ifnarch %{ix86}
make check
%endif

%files -n %{libname}
%{_libdir}/libmpfr.so.%{major}*

%files -n %{devname}
%{_includedir}/mpfr.h
%{_includedir}/mpf2mpfr.h
%{_infodir}/mpfr.info*
%{_libdir}/libmpfr.so
%{_libdir}/pkgconfig/mpfr.pc

%files -n %{statname}
%{_libdir}/libmpfr.a
