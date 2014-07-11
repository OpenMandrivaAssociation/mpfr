%define major 4
%define libname	%mklibname %{name} %{major}
%define devname	%mklibname %{name} -d
%define statname %mklibname %{name} -d -s
%bcond_with	crosscompile

Summary:	Multiple-precision floating-point computations with correct rounding
Name:		mpfr
Version:	3.1.2
Release:	9
License:	LGPLv3+
Group:		System/Libraries
Url:		http://www.mpfr.org/
Source0:	http://www.mpfr.org/mpfr-current/mpfr-%{version}.tar.xz
BuildRequires:	gmp-devel

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
%setup -q

%build
%configure2_5x \
	--enable-shared \
	--enable-static \
%if %{with crosscompile}
	--with-gmp-lib=%{_prefix}/%{_target_platform}/sys-root%{_libdir} \
%endif
	--enable-thread-safe

%make

%install
%makeinstall_std

rm -rf installed-docs
mv %{buildroot}%{_docdir}/%{name} installed-docs

%check
make check

%files -n %{libname}
%{_libdir}/libmpfr.so.%{major}*

%files -n %{devname}
%doc installed-docs/*
%{_includedir}/mpfr.h
%{_includedir}/mpf2mpfr.h
%{_infodir}/mpfr.info*
%{_libdir}/libmpfr.so

%files -n %{statname}
%{_libdir}/libmpfr.a

