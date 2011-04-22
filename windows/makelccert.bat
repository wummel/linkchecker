:: File to generate a code signing certificate for LinkChecker
:: Needs makecert.exe and pkv2pfx.exe installed in the PATH
makecert -r -pe -n "CN=LinkChecker certificate" -b 01/01/2011 -e 01/01/2021 -eku 1.3.6.1.5.5.7.3.3 -sv linkchecker.pvk linkchecker.cer
pvk2pfx -pvk linkchecker.pvk -spc linkchecker.cer -pfx linkchecker.pfx
