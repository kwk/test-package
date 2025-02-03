Name:           test-package
Version:        2.0.0
Release:        1%{?dist}
Summary:        Tiny package to test some things

License:        BSD-3-Clause

%global _description %{expand:
test-package is a package to test out various packaging
ideas, problems, concepts etc.}

%description %_description

%prep
# Nothing to do here


%build
# Nothing to build

%install
# Unversioned files
%if "%{version}" == "1.0.0"
mkdir -pv %{buildroot}/%{_libdir}/%{name}
echo "This is just an idea" > %{buildroot}/%{_libdir}/%{name}/idea.txt
%endif

# Verioned files
%if "%{version}" == "2.0.0"
mkdir -pv %{buildroot}/%{_libdir}/%{name}%{version}
ln -sv %{name}%{version} %{buildroot}%{_libdir}/%{name}
echo "This is just an idea" > %{buildroot}/%{_libdir}/%{name}%{version}/idea.txt
%endif


# The pretrans_rpmmove_dirs macro exists for packages to replace directories
# with symbolic links which normally is not possible with RPM. The trick is to
# use the generated scriptlet below to rename existing directories before
# replacing them with a symbolic link.
#
# Make sure you call this macro at the end of a %%files section for a package.
# This macro will then automatically add the %%ghost entries for the moved
# paths for you.
#
# When building in compat mode, the pretrans_rpmmove_dirs macro does nothing.
#
# See this page for a detailed problem description:
# https://docs.fedoraproject.org/en-US/packaging-guidelines/Directory_Replacement/
%if %{with compat_build}
%define pretrans_rpmmove_dirs(n:) %{nil}
%else
%define pretrans_rpmmove_dirs(n:) %{lua:
local packagename = string.gsub(rpm.expand("%{-n*}"), "%s*", "")
local paths_str = '"'..string.gsub(rpm.expand("%*"), "%s+", '",\\n"')

paths_str = string.sub(paths_str,0,-4)

for i = 1, rpm.expand("%#") do
    print('%ghost '..string.gsub(rpm.expand([[%]]..i), "%s+", "")..'.rpmmoved\\n') \
end

print("\\n%pretrans -n " .. packagename .. " -p <lua> \\n")
print("local paths={\\n")
print(paths_str..'\\n')
print("}\\n")
print([[
print("Running pretrans! YAY!")
for _, path in ipairs(paths) do
  print('Handling path:'..path)
  st = posix.stat(path)
  if st and st.type == "directory" then
    status = os.rename(path, path .. ".rpmmoved")
    if not status then
      suffix = 0
      while not status do
        suffix = suffix + 1
        status = os.rename(path .. ".rpmmoved", path .. ".rpmmoved." .. suffix)
      end
      os.rename(path, path .. ".rpmmoved")
    end
  end
  if st and st.type == "link" then
    assert(os.remove(path..'non-existing'))
  end
end
]])
-- Remove the following "end" and you'll get this error:
-- error: invalid syntax in lua scriptlet: [string "%pretrans"]:20: unexpected symbol near '#'
print("\\n%end")
}
%endif

%check
# Nothing to check

%files
# Unversioned files
%if "%{version}" == "1.0.0"
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/idea.txt
%endif

# Versioned files
%if "%{version}" == "2.0.0"
%dir %{_libdir}/%{name}%{version}
%{_libdir}/%{name}%{version}/idea.txt
%{_libdir}/%{name}
%endif

# Deal with change of dir to link
%if "%{version}" == "1.0.0"
%pretrans -n %{name} -p <lua>
print('Pretrans for '..rpm.expand("%{name}-%{version}"))
local path = rpm.expand("%{_libdir}/%{name}")
st = posix.stat(path)
if st and st.type == "link" then
  assert(os.remove(path..'-not-existing'))
  # This will provoke an error in case of a downgrade that says:
  #
  #   Error in pre-transaction scriptlet: test-package-0:1.0.0-1.fc41.x86_64
  #   [RPM] lua script failed: [string "%pretrans(test-package-1.0.0-1.fc41.x86_64)"]:5: /usr/lib64/test-package-not-existing: No such file or directory
  #
  # This is perfect because it is exactly what we need: The confirmation of what file will be deleted.
end
%end
%endif

%if "%{version}" == "2.0.0"
%{pretrans_rpmmove_dirs -n %{name}
  %{_libdir}/%{name}
}
%endif

# https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_syntax
%pre
echo "%{name}-%{version} Pre Code: $1"
if [ $1 -gt 1 ] ; then
  echo "According to documentation, this is an upgrade"
fi
if [ $1 -eq 1 ] ; then
  echo "According to documentation, this is an install"
fi

%preun
echo "%{name}-%{version} Preun Code: $1"
if [ $1 -eq 0 ] ; then
  echo "According to documentation, this is an uninstall"
fi
if [ $1 -eq 1 ] ; then
  echo "According to documentation, this is an upgrade"
fi

%changelog

%changelog
* Mon Feb 03 2025 Konrad Kleine <kkleine@redhat.com> - 2.0.0-1
- Version 2

* Mon Feb 03 2025 Konrad Kleine <kkleine@redhat.com> - 1.0.0-1
- Version 1