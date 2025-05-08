# move-queue-msgs
# Copy/Move messages between Solace Queues
#  Use --copy-only to copy messages (leave messages in source queue)
#  Default is to move messages (delete from source queue)
#  Max Page size is 100 (SEMP limitation?). Can't move more than 100 messages in one run
#
#  The would loop if there are more than PageSize messages.
#  The script can run forever if there are more than PageSize messages in the source queue
#
# Ramesh Natarajan (nram), Solace
# ###########################################################################################

import sys, os
import argparse
import pprint
import json
from urllib.parse import unquote, quote # for Python 3.7

sys.path.insert(0, os.path.abspath("."))
from common import SempHandler
from common import YamlHandler
from common import LogHandler

# suppress TLS warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    
me = "bulk-msg-move"
ver = '1.0'

# Globals
Cfg = {}    # global handy config dict
Verbose = 0
Copy_only = False # default is to move messages (delete from source queue)
Prompt = "moving"
prompted = "moved"
pp = pprint.PrettyPrinter(indent=4)

def main(argv):
    """ program entry drop point """
    global Cfg, Verbose, Copy_only, Prompt, prompted

    p = argparse.ArgumentParser()
    p.add_argument('--config', dest="config_file", required=True, help='config json file') 
    p.add_argument( '--verbose', '-v', action="count",  required=False, default=0,
                help='Verbose output. use -vvv for tracing')
    p.add_argument('--copy-only', dest="copy_only", action='store_true', required=False, default=False, 
                   help='Leave messages in the source queue after copy (Default: DELETE))')
    r = p.parse_args()

    print ('\n{}-{} Starting\n'.format(me,ver))

    Verbose = r.verbose
    Copy_only = r.copy_only
    if Copy_only:
        Prompt = "copying"
        prompted = "copied"

    print ("Reading user config file  : {}".format(r.config_file))
    yaml_h = YamlHandler.YamlHandler()
    Cfg = yaml_h.read_config_file(r.config_file)

    sys_cfg_file = Cfg["internal"]["systemConfig"]
    print ("Reading system config file: {}".format(sys_cfg_file))

    system_config_all = yaml_h.read_config_file (sys_cfg_file)
    
    Cfg['system'] = system_config_all.copy() # store system cfg in the global Cfg dict
    Cfg['script_name'] = me
    Cfg['verbose'] = Verbose

    log_h = LogHandler.LogHandler(Cfg)
    log = log_h.get()
    log.info('Starting {}-{}'.format(me, ver))
    log.debug ('SYSTEM CONFIG : {}'.format(json.dumps(system_config_all, indent=4)))
    log.info ('SYSTEM CONFIG : {}'.format(json.dumps(system_config_all, indent=4)))
    log.info ('USER CONFIG   : {}'.format(json.dumps(Cfg, indent=4)))
    # add this after dumping Cfg. josn.dumps() can't handle log object
    Cfg['log_handler'] = log_h
      

    vpn = Cfg["vpn"]["msgVpnNames"][0]
    src_q = Cfg["queues"]["source"]
    dest_q = Cfg["queues"]["destination"]
    print ("{} Msgs from Queue {} -> {} in VPN {}".format(Prompt, src_q, dest_q, vpn))
    vpn_json_file = copy_or_move_msgs (vpn, src_q, dest_q)

def copy_or_move_msgs (vpn, src_q, dest_q):

    global Verbose, Copy_only

    if Verbose:
        print ("copy_or_move_msgs: vpn: {} src_q: {} dest_q: {}".format(vpn, src_q, dest_q))

    rtr_cfg = Cfg["router"]
    sys_cfg = Cfg["system"]
    if Verbose > 2:
        print ('--- ROUTER :\n', json.dumps(rtr_cfg))
        print ('--- SYSTEM :\n', json.dumps(sys_cfg))

    semp_h = SempHandler.SempHandler(Cfg)

    # Get list of replicationGroupMsgId's from source queue
    page_sz = sys_cfg["semp"]["pageSize"]
    if page_sz > 100:
        print (f"*** Page size {page_sz} too big. Setting to 100 ***")
        page_sz = 100

    m_url = "{}/{}/msgVpns/{}".format(rtr_cfg["sempUrl"], sys_cfg["semp"]["monitorUrl"], vpn )
    a_url = "{}/{}/msgVpns/{}".format(rtr_cfg["sempUrl"], sys_cfg["semp"]["actionUrl"], vpn )
    query_url = "{}/queues/{}/msgs?select=msgId,replicationGroupMsgId&count={}".format(unquote(m_url), quote(src_q, safe=''), page_sz)
    copy_url = "{}/queues/{}/copyMsgFromQueue".format(unquote(a_url), quote(dest_q, safe=''))


    if Verbose > 2:
        print("   Get URL {} (PageSize: {})".format(query_url, page_sz))

 
    lc = 0 # loop counter
    tn = 0 # total messages procesed
    done = False
    while (not done) :
        lc += 1
        resp = semp_h.http_get(query_url) 
        if Verbose > 2:
            print("Get: req.json()")
            pp.pprint(resp.json()['data'])
        if (resp.status_code != 200):
            print(resp.text)
            raise RuntimeError

        # check if we got any messages to move    
        if len(resp.json()['data']) == 0:
            print (f"[{lc}] No more messages in {src_q}")
            done = True
            break
        
        # ok we got some msgs to move
        # build the move url
        nmsgs = len(resp.json()['data'])
        n = 1
        print ("[{}] Got {} messages from queue {}".format(lc, len(resp.json()['data']), src_q))
        # loop thru the list of replicationGroupMsgId's and move them
        for msg in resp.json()['data']:
            msg_id = msg['msgId']
            rgm_id = msg['replicationGroupMsgId']
            body = { "replicationGroupMsgId": rgm_id , "sourceQueueName": src_q }

            if Verbose:
                print (" - {} msg {} of {} ({}) (Msg Id: {}, ID: {})".format(Prompt, n, nmsgs, lc, msg_id, rgm_id))
            n += 1
            tn += 1
            if Verbose:
                print ("   Copy message {} to {}".format(rgm_id, dest_q))
            if Verbose > 2:
                print ("msg: {}".format(msg))

            # first copy the message
            if Verbose > 2:
                print ("   Copy URL (PUT) {}".format(copy_url)) 
                print ("   Copy body: {}".format(body))

            resp = semp_h.http_put(copy_url, body)
            if Verbose > 2:
                print("Post: resp.json()")
                pp.pprint(resp.json())
            if (resp.status_code != 200):
                print (f"   *** Copy msg {msg_id} to {dest_q} failed. Leaving message in source queue {src_q} ***")
                if Verbose > 2:
                    print(resp.text)
                continue

            # Now delete from source queue -  use msgId (not replicationGroupMsgId)
            if Copy_only:
                done = True
                continue
            
            if Verbose:
                print ("   * Delete message {} from {}".format(msg_id, src_q))

            delete_url = "{}/queues/{}/msgs/{}/delete".format(unquote(a_url), quote(src_q, safe=''), msg_id)
            if Verbose > 2:
                print("   Delete URL (PUT) {}".format(delete_url))
            body = {}

            resp = semp_h.http_put (delete_url, body)
            if Verbose > 2:
                print("Delete: resp.json()")
                pp.pprint(resp.json())
            if (resp.status_code != 200):
                print(resp.text)
                continue
    print (f"\nDone {Prompt} messages.\n{tn} messages {prompted} from {src_q} -> {dest_q}")
    
        
# Program entry point
if __name__ == "__main__":
    """ program entry point - must be  below main() """

    main(sys.argv[1:])