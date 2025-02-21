# Copy or Move messages between Solace Queues

Script to either copy or move messages between queues on a Solace broker. This script uses combination SEMP monitor and config APIs.

## References
- [Solace PubSub+](https://docs.solace.com/Get-Started/get-started-lp.htm)
- [SEMP](https://docs.solace.com/Admin/SEMP/Using-SEMP.htm)


## Requirements
See requirements.txt

## Installing

Using virtual env is optional, but recommended if you want to keep the dependencies isolated
```
▶ python3 -m venv venv
▶ source venv/bin/activate
```

Check all required modules are in place or install them.
```
▶ pip install -r requirements.txt
```

## Config
See sample-configs-*

# Running

### Moving messages between Queues

``` sh
▶ python3 bulk-msg-move.py --config sample-config-local.yaml            

bulk-msg-move-1.0 Starting

Reading user config file  : sample-config-local.yaml
Reading system config file: config/system.yaml
Opening log file for bulk-msg-move : ./logs/bulk-msg-move-20240322-163651.log
moving Msgs from Queue DMQ.TestQ -> TestQ in VPN default
[1] Got 100 messages from queue DMQ.TestQ
...
[20] Got 100 messages from queue DMQ.TestQ
[21] Got 99 messages from queue DMQ.TestQ
[22] No more messages in DMQ.TestQ

Done moving messages.
2099 messages moved from DMQ.TestQ -> TestQ
 ```


 ## Copying messages between Queues

``` sh
▶ python3 bulk-msg-move.py --config sample-config-local.yaml --copy-only

bulk-msg-move-1.0 Starting

Reading user config file  : sample-config-local.yaml
Reading system config file: config/system.yaml
Opening log file for bulk-msg-move : ./logs/bulk-msg-move-20240322-163229.log
copying Msgs from Queue DMQ.TestQ -> TestQ in VPN default
[1] Got 100 messages from queue DMQ.TestQ

Done copying messages.
100 messages copied from DMQ.TestQ -> TestQ
```