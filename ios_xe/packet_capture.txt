1. Define the location where the capture will occur

`monitor capture CAP interface GigabitEthernet0/0/1 both`

2. Associate a filter. The filter may be specified inline, or an ACL or class-map can be referenced:

 `monitor capture CAP match ipv4 protocol tcp any any`
 
3. Start the capture:

 `monitor capture CAP start`

4. The capture is now active. Allow collection of the necessary data

5. Stop the capture

 `monitor capture CAP stop`

6. Examine the buffer

 `show monitor capture CAP buffer brief`

7. Examine the capture in a detailed view:

 `show monitor capture CAP buffer detailed` 

### Export

 `monitor capture CAP export ftp://10.0.0.1/CAP.pcap`

## Stop capture 

 `no monitor capture CAP`

