@echo off
echo Opening ports on Windows Firewall...

netsh advfirewall firewall add rule name="Sea Level Backend" dir=in action=allow protocol=TCP localport=30886
netsh advfirewall firewall add rule name="Sea Level Frontend" dir=in action=allow protocol=TCP localport=30887
netsh advfirewall firewall add rule name="Sea Level Port 30888" dir=in action=allow protocol=TCP localport=30888
netsh advfirewall firewall add rule name="Sea Level Port 30889" dir=in action=allow protocol=TCP localport=30889
netsh advfirewall firewall add rule name="Sea Level Port 30890" dir=in action=allow protocol=TCP localport=30890

echo All ports opened successfully!
pause