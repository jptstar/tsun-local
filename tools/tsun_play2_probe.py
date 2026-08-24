#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Sunology PLAY2 all-in-one READ-ONLY diagnostic probe.
Python 3.10+, standard library only. Produces JSON + LOG.
No config writes, no BLE/Wi-Fi provisioning, no cloud login, no Modbus writes.
"""
from __future__ import annotations
import argparse,base64,hashlib,http.client,json,math,re,secrets,socket,ssl,struct,sys,time
from datetime import datetime,timezone
from ipaddress import IPv4Address,ip_network
from pathlib import Path

VER="1.2.1"; SCHEMA=4
UDP_PORTS=(48899,49999); TCP_PORTS=(8899,48899,49999)
SMART=b"smartlinkfind"; LEGACY=(b"WIFIKIT-214028-READ",b"HF-A11ASSISTHREAD",b"devicelinkfind")
MDNS="224.0.0.251"; MDNS_PORT=5353; SERVICE="_solarhome._tcp.local."; HUB_PREFIX="sunology-hb-"
HTTP_PATHS=("/index_cn.html","/index.html","/status.html","/")
SN_RE=re.compile(r"(?<!\d)([1-9]\d{7,9})(?!\d)")
IP_RE=re.compile(r"(?<!\d)(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?!\d)")
MAC_RE=re.compile(r"(?i)(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}")

class Log:
 def __init__(self,p): self.f=open(p,"w",encoding="utf-8")
 def w(self,s=""): print(s); self.f.write(s+"\n"); self.f.flush()
 def close(self): self.f.close()

class Hosts:
 def __init__(self,host): self.d={host:{"alias":"host0","reasons":["supplied_host"],"strong":True}}
 def add(self,ip,why,strong=False):
  try: IPv4Address(ip)
  except Exception:return
  if ip not in self.d and len(self.d)<8:self.d[ip]={"alias":f"candidate{len(self.d)}","reasons":[],"strong":False}
  if ip in self.d:
   if why not in self.d[ip]["reasons"]:self.d[ip]["reasons"].append(why)
   self.d[ip]["strong"]|=strong
 def alias(self,ip): return self.d.get(ip,{}).get("alias","other-local-host")
 def public(self): return [{"alias":v["alias"],"reasons":v["reasons"],"strong":v["strong"]} for v in self.d.values()]

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def crc16(b):
 c=0xffff
 for x in b:
  c^=x
  for _ in range(8):c=(c>>1)^0xa001 if c&1 else c>>1
 return c&0xffff
def redact(b,sn,ips):
 r=bytes(b)
 if sn:
  for x in (str(sn).encode(),sn.to_bytes(4,"little"),sn.to_bytes(4,"big")):r=r.replace(x,b"*"*len(x))
 for ip in ips:
  r=r.replace(ip.encode(),b"*"*len(ip))
  try:r=r.replace(socket.inet_aton(ip),b"****")
  except OSError:pass
 t=r.decode("latin1","ignore")
 for m in list(MAC_RE.finditer(t)):r=r.replace(m.group().encode("latin1"),b"*"*len(m.group()))
 return r
def evidence(b,sn,ips):
 r=redact(b,sn,ips); cap=r[:4096]
 return {"length":len(b),"sha256":sha(b),"redacted_hex":cap.hex(),"redacted_ascii":"".join(chr(x) if 32<=x<127 else f"\\x{x:02x}" for x in cap),"complete":len(b)<=4096}
def err(stage,e):return {"stage":stage,"type":type(e).__name__,"detail":str(e) or type(e).__name__}

def parse_udp(b):
 t=b.decode("utf-8","replace").strip("\x00\r\n "); out={"text":t,"format":"text","sn":None,"ip":None,"mac":None}
 try:o=json.loads(t)
 except Exception:o=None
 if isinstance(o,dict):
  out["format"]="json"
  for k in ("mid","sn","serial","loggerSn","monitorSn"):
   try:n=int(str(o.get(k,"")))
   except Exception:continue
   if 0<n<=0xffffffff:out["sn"]=n;break
  if isinstance(o.get("ip"),str) and IP_RE.fullmatch(o["ip"]):out["ip"]=o["ip"]
  if isinstance(o.get("mac"),str) and MAC_RE.fullmatch(o["mac"]):out["mac"]=o["mac"]
  return out
 lo=t.lower()
 if "smart_config" in lo or "smartconfig" in lo:out["format"]="smart_config_text"
 elif "smartlink" in lo:out["format"]="smartlink_text"
 m=SN_RE.search(t); out["sn"]=int(m.group()) if m else None
 m=IP_RE.search(t); out["ip"]=m.group() if m else None
 m=MAC_RE.search(t); out["mac"]=m.group() if m else None
 return out

def smart_fields(t,sn):
 lo=t.lower(); p=lo.find("smart_config"); prefix="smart_config"
 if p<0:p=lo.find("smartconfig");prefix="smartconfig"
 if p<0:return None
 tail=t[p+len(prefix):].strip("\x00\r\n #"); fs=tail.split("##") if tail else []
 def safe(x):
  if sn:x=x.replace(str(sn),"<MONITOR_SN>")
  x=IP_RE.sub("<LOCAL_IP>",x);x=MAC_RE.sub("<MAC>",x);x=SN_RE.sub("<SERIAL>",x);return x
 return {"prefix":prefix,"separator":"##","field_count":len(fs),"fields":[{"index":i,"length":len(x),"value_redacted":safe(x)} for i,x in enumerate(fs)]}

def udp_variant(host,bindp,sendp,msgs,timeout):
 R={"bind_port":bindp,"send_port":sendp,"messages":[x.decode() for x in msgs],"bound":False,"replies":[],"error":None}
 s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
 try:
  try:s.bind(("",bindp));R["bound"]=True
  except OSError as e:R["error"]=err("bind",e);return R
  if bindp==49999 and sendp==48899:
   try:s.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,socket.inet_aton("239.0.0.0")+socket.inet_aton("0.0.0.0"))
   except OSError:pass
  dst=(host,str(ip_network(f"{host}/24",strict=False).broadcast_address),"255.255.255.255")
  for d in dst:
   for m in msgs:
    try:s.sendto(m,(d,sendp))
    except OSError:pass
  end=time.monotonic()+timeout; seen=set()
  while (left:=end-time.monotonic())>0:
   s.settimeout(left)
   try:b,(src,sp)=s.recvfrom(8192)
   except socket.timeout:break
   except OSError as e:R["error"]=err("recv",e);break
   if b in msgs:continue
   k=(src,sp,sha(b))
   if k in seen:continue
   seen.add(k);R["replies"].append({"_src":src,"source_port":sp,"_raw":b,"_p":parse_udp(b)})
 finally:s.close()
 return R

def udp_all(host,timeout):
 out=[]
 for bp in UDP_PORTS:
  for sp in UDP_PORTS:
   for name,msgs in (("smartlink",(SMART,)),("legacy",LEGACY)):
    r=udp_variant(host,bp,sp,msgs,timeout);r["name"]=f"udp_{bp}_to_{sp}_{name}";out.append(r)
 return out

def dn(name):
 return b"".join(bytes((len(x),))+x.encode() for x in name.rstrip(".").split("."))+b"\0"
def rdname(b,o,seen=None):
 seen=set() if seen is None else seen;ls=[];nxt=None
 while True:
  n=b[o]
  if n==0:return ".".join(ls)+".",(nxt if nxt is not None else o+1)
  if n&0xc0==0xc0:
   p=((n&0x3f)<<8)|b[o+1]
   if p in seen:raise ValueError("dns loop")
   seen.add(p);nxt=o+2 if nxt is None else nxt;o=p;continue
  o+=1;ls.append(b[o:o+n].decode("utf8","replace"));o+=n

def mdns(timeout):
 q=struct.pack("!HHHHHH",0,0,1,0,0,0)+dn(SERVICE)+struct.pack("!HH",12,1); packets=[]; errors=[]
 s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP);s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
 try:
  try:s.bind(("",5353));s.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,socket.inet_aton(MDNS)+socket.inet_aton("0.0.0.0"));mode="5353_multicast"
  except OSError as e:errors.append(err("mdns_bind",e));s.close();s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.bind(("",0));mode="ephemeral"
  s.sendto(q,(MDNS,5353));end=time.monotonic()+timeout
  while (left:=end-time.monotonic())>0:
   s.settimeout(left)
   try:b,(src,sp)=s.recvfrom(9000)
   except socket.timeout:break
   packets.append((b,src,sp))
 finally:s.close()
 srv={};A={};ptr=set();txt={}
 for b,src,sp in packets:
  try:
   _,_,qd,an,ns,ar=struct.unpack_from("!HHHHHH",b,0);o=12
   for _ in range(qd):_,o=rdname(b,o);o+=4
   for _ in range(an+ns+ar):
    name,o=rdname(b,o);typ,cl,ttl,l=struct.unpack_from("!HHIH",b,o);o+=10;rs=o;re_=o+l
    if typ==12:target,_=rdname(b,rs);ptr.add(target)
    elif typ==33 and l>=6:
     _,_,port=struct.unpack_from("!HHH",b,rs);target,_=rdname(b,rs+6);srv[name]=(port,target)
    elif typ==1 and l==4:A.setdefault(name,set()).add(socket.inet_ntoa(b[rs:re_]))
    elif typ==16:
     cur=rs;arr=[]
     while cur<re_:n=b[cur];cur+=1;arr.append(b[cur:cur+n].decode("utf8","replace"));cur+=n
     txt[name]=arr
    o=re_
  except Exception:continue
 services=[]
 for ins in sorted(ptr|set(srv)):
  port,target=srv.get(ins,(None,None));services.append({"instance":ins,"port":port,"addresses":sorted(A.get(target,set())) if target else [],"txt":txt.get(ins,[]),"hub_name":ins.lower().startswith(HUB_PREFIX)})
 return {"mode":mode,"packet_count":len(packets),"services":services[:8],"errors":errors}

def websocket(host,port,timeout,listen,sn,ips):
 R={"port":port,"connected":False,"events":[],"errors":[]}
 for origin in (None,"http://localhost","capacitor://localhost"):
  key=base64.b64encode(secrets.token_bytes(16)).decode();h=["GET /ws HTTP/1.1",f"Host: {host}:{port}","Upgrade: websocket","Connection: Upgrade",f"Sec-WebSocket-Key: {key}","Sec-WebSocket-Version: 13"]
  if origin:h.append(f"Origin: {origin}")
  try:
   with socket.create_connection((host,port),timeout=timeout) as s:
    s.settimeout(timeout);s.sendall(("\r\n".join(h)+"\r\n\r\n").encode());r=b""
    while b"\r\n\r\n" not in r and len(r)<16384:r+=s.recv(2048)
    status=r.decode("latin1","replace").split("\r\n",1)[0]
    if " 101 " not in f" {status} ":R["errors"].append({"origin":origin,"status":status});continue
    R["connected"]=True;R["origin"]=origin;R["status"]=status;end=time.monotonic()+listen
    def rx(n):
     z=b""
     while len(z)<n:
      x=s.recv(n-len(z))
      if not x:raise EOFError
      z+=x
     return z
    while len(R["events"])<24 and (left:=end-time.monotonic())>0:
     s.settimeout(min(1.5,left))
     try:a=rx(2)
     except socket.timeout:continue
     except EOFError:break
     op=a[0]&15;n=a[1]&127;masked=a[1]&128
     if n==126:n=int.from_bytes(rx(2),"big")
     elif n==127:n=int.from_bytes(rx(8),"big")
     if n>16384:break
     mask=rx(4) if masked else b"";p=rx(n)
     if masked:p=bytes(x^mask[i%4] for i,x in enumerate(p))
     ev={"opcode":op,"payload":evidence(p,sn,ips)}
     if op==1:
      try:o=json.loads(p.decode("utf8","replace"))
      except Exception:o=None
      if isinstance(o,dict):
       d=o.get("data") if isinstance(o.get("data"),dict) else o;ev["event"]=o.get("event") or o.get("type");ev["signals"]={k:d[k] for k in ("pvP","power","production","soc","batteryPower","gridPower","state","deviceState") if k in d and isinstance(d[k],(int,float,str,bool,type(None)))}
     R["events"].append(ev)
     if op==8:break
    return R
  except Exception as e:R["errors"].append(err("websocket",e))
 return R

def isopen(host,port,t):
 try:
  with socket.create_connection((host,port),timeout=t):return True
 except OSError:return False

def http_id(host,t,sn,ips):
 out=[]
 for port,tls in ((80,False),(443,True)):
  tr={"scheme":"https" if tls else "http","open":isopen(host,port,min(t,1.2)),"pages":[]}
  if tr["open"]:
   for path in HTTP_PATHS:
    try:
     if tls:
      ctx=ssl.create_default_context();ctx.check_hostname=False;ctx.verify_mode=ssl.CERT_NONE;c=http.client.HTTPSConnection(host,port,timeout=t,context=ctx)
     else:c=http.client.HTTPConnection(host,port,timeout=t)
     c.request("GET",path,headers={"Connection":"close","User-Agent":"TSUN-Local-PLAY2-Probe"});r=c.getresponse();b=r.read(524289);tr["pages"].append({"path":path,"status":r.status,"server":r.getheader("Server"),"content_type":r.getheader("Content-Type"),"body":evidence(b,sn,ips) if len(b)<=524288 else None});c.close()
    except Exception as e:tr["pages"].append({"path":path,"error":err("http",e)})
  out.append(tr)
 return out

def mbread(addr,count=1):
 b=b"\x01\x03"+addr.to_bytes(2,"big")+count.to_bytes(2,"big");return b+crc16(b).to_bytes(2,"little")
def mbtcp(addr,count=1,tx=1):
 p=b"\x01\x03"+addr.to_bytes(2,"big")+count.to_bytes(2,"big");return struct.pack("!HHH",tx,0,len(p))+p
def r1511(tag,fn,start,end):
 n=end-start+1;b=bytes((tag,fn,0))+start.to_bytes(2,"big")+b"\x00\x02"+n.to_bytes(2,"big");return b+crc16(b).to_bytes(2,"big")
def ap(sn,p,sl=0,seq=0):
 d=b"\x02"+sl.to_bytes(2,"little")+bytes(12)+p;x=len(d).to_bytes(2,"little")+b"\x10\x45"+seq.to_bytes(2,"little")+sn.to_bytes(4,"little")+d;return b"\xa5"+x+bytes((sum(x)&255,0x15))
def probes(sn):
 q=[]
 for S in ([0,sn] if sn else [0]):
  for name,p,sl in (("1511",r1511(0xa1,1,0x0bb8,0x0bd0),0),("1511_sl",r1511(0xa1,1,0x0bb8,0x0bd0),0x1511),("02b0",mbread(0x3009,22),0x02b0),("1097",mbread(0x1100),0x1097),("3026",mbread(0,45),0x3026)):
   for seq in (0,1):q.append((f"ap_{name}_sn{'0' if S==0 else 'supplied'}_seq{seq}",ap(S,p,sl,seq),{"kind":"AP","sensor_list":f"0x{sl:04X}","sn_zero":S==0,"seq":seq}))
 q += [("direct_rtu_02b0",mbread(0x3000),{"kind":"RTU-FC03"}),("direct_rtu_1097",mbread(0x1100),{"kind":"RTU-FC03"}),("direct_tcp_02b0",mbtcp(0x3000),{"kind":"Modbus-TCP-FC03"}),("direct_1511",r1511(0xa1,1,0x0bb8,0x0bd0),{"kind":"1511-read"})]
 return q

def tcp_one(host,port,name,req,meta,t,sn,ips):
 R={"name":name,"meta":meta,"connected":False,"sent":False,"response_length":0};start=time.monotonic()
 try:
  with socket.create_connection((host,port),timeout=t) as s:
   R["connected"]=True;s.settimeout(t);s.sendall(req);R["sent"]=True;z=b""
   try:
    while len(z)<65536:
     x=s.recv(min(4096,65536-len(z)))
     if not x:break
     z+=x
     if z: s.settimeout(.25)
   except socket.timeout:pass
   R["response_length"]=len(z);R["outcome"]="bytes" if z else "no_bytes"
   if z:R["response"]=evidence(z,sn,ips)
 except Exception as e:R["outcome"]="error";R["error"]=err("tcp",e)
 R["elapsed_ms"]=round((time.monotonic()-start)*1000,1);return R

def tcp_port(host,port,t,sn,ips):
 R={"port":port,"open":isopen(host,port,min(t,1.2)),"passive":None,"probes":[]}
 if not R["open"]:return R
 try:
  with socket.create_connection((host,port),timeout=t) as s:
   s.settimeout(min(t,1));
   try:b=s.recv(1024)
   except socket.timeout:b=b""
   R["passive"]={"received":bool(b),"payload":evidence(b,sn,ips) if b else None}
 except Exception as e:R["passive"]={"error":err("passive",e)}
 for name,req,meta in probes(sn):R["probes"].append(tcp_one(host,port,name,req,meta,t,sn,ips))
 return R

def main():
 if sys.version_info<(3,10):print("Python 3.10+ required",file=sys.stderr);return 2
 p=argparse.ArgumentParser();p.add_argument("--host",required=True);p.add_argument("--monitor-sn","--serial",dest="sn",type=int);p.add_argument("--udp-timeout",type=float,default=3);p.add_argument("--mdns-timeout",type=float,default=8);p.add_argument("--ws-listen",type=float,default=8);p.add_argument("--timeout",type=float,default=1.8);p.add_argument("--http-timeout",type=float,default=1.8);p.add_argument("--output",type=Path);a=p.parse_args()
 try:IPv4Address(a.host)
 except ValueError:print("Invalid --host",file=sys.stderr);return 2
 stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ");jp=a.output or Path(f"tsun_play2_superprobe_{stamp}.json");lp=jp.with_suffix(".log");L=Log(lp);H=Hosts(a.host)
 D={"format":"tsun-local-play2-superprobe","schema_version":SCHEMA,"metadata":{"tool_version":VER,"timestamp_utc":now(),"read_only":True,"writes":0,"apk_evidence":{"smartlink":"UDP 48899/49999","smart_config":"prefix + ## fields","mdns":"_solarhome._tcp.local","websocket":"/ws","mock_only":"ws://127.0.0.1:20199"}},"udp":[],"mdns":{},"websocket":[],"http":[],"tcp":[],"candidates":[],"errors":[]}
 L.w(f"TSUN Local PLAY2 Super-Probe v{VER} - READ-ONLY");L.w("UDP cross-matrix 48899/49999 + mDNS + WebSocket + HTTP(S) + same TCP matrix on 8899/48899/49999")
 try:
  U=udp_all(a.host,a.udp_timeout)
  for r in U:
   for x in r["replies"]:
    pp=x["_p"];match=bool(a.sn and pp.get("sn")==a.sn);H.add(x["_src"],f"udp:{r['name']}",match)
    if pp.get("ip"):H.add(pp["ip"],f"udp-declared:{r['name']}",match)
  for r in U:
   pub={k:v for k,v in r.items() if k!="replies"};pub["replies"]=[]
   for x in r["replies"]:
    pp=x["_p"];pub["replies"].append({"source_alias":H.alias(x["_src"]),"source_port":x["source_port"],"format":pp["format"],"sn_present":pp.get("sn") is not None,"sn_matches":bool(a.sn and pp.get("sn")==a.sn),"declared_ip_alias":H.alias(pp["ip"]) if pp.get("ip") else None,"mac_present":pp.get("mac") is not None,"smart_config":smart_fields(pp["text"],a.sn),"payload":evidence(x["_raw"],a.sn,H.d)})
   D["udp"].append(pub);L.w(f"UDP {r['name']}: {len(pub['replies'])} replies")
 except Exception as e:D["errors"].append(err("udp",e))
 try:
  M=mdns(a.mdns_timeout)
  for s in M["services"]:
   for ip in s["addresses"]:H.add(ip,"mdns")
  D["mdns"]={"mode":M["mode"],"packet_count":M["packet_count"],"errors":M["errors"],"services":[{"instance":"<sunology-hb>" if s["hub_name"] else "<service>","port":s["port"],"address_aliases":[H.alias(x) for x in s["addresses"]],"hub_name":s["hub_name"],"txt":s["txt"]} for s in M["services"]]};L.w(f"mDNS services: {len(M['services'])}")
  for s in M["services"]:
   if isinstance(s["port"],int):
    for ip in s["addresses"][:2]:
     w=websocket(ip,s["port"],a.timeout,a.ws_listen,a.sn,H.d);w["host_alias"]=H.alias(ip);D["websocket"].append(w);L.w(f"WS {H.alias(ip)}:{s['port']}: connected={w['connected']} events={len(w['events'])}")
 except Exception as e:D["errors"].append(err("mdns/ws",e))
 D["candidates"]=H.public()
 for ip,v in list(H.d.items()):
  try:D["http"].append({"host_alias":v["alias"],"transports":http_id(ip,a.http_timeout,a.sn,H.d)})
  except Exception as e:D["errors"].append(err("http",e))
  for port in TCP_PORTS:
   try:
    r=tcp_port(ip,port,a.timeout,a.sn,H.d);r["host_alias"]=v["alias"];D["tcp"].append(r);L.w(f"TCP {v['alias']}:{port}: open={r['open']} replies={sum(1 for q in r['probes'] if q.get('response_length'))}")
   except Exception as e:D["errors"].append(err(f"tcp:{port}",e))
 D["summary"]={"udp_variants":len(D["udp"]),"udp_replies":sum(len(x["replies"]) for x in D["udp"]),"candidates":len(D["candidates"]),"mdns_services":len(D.get("mdns",{}).get("services",[])),"ws_connections":sum(1 for x in D["websocket"] if x["connected"]),"tcp_open":{str(p):sum(1 for x in D["tcp"] if x["port"]==p and x["open"]) for p in TCP_PORTS},"tcp_responses":{str(p):sum(1 for x in D["tcp"] if x["port"]==p for q in x["probes"] if q.get("response_length")) for p in TCP_PORTS}}
 D["metadata"]["timestamp_utc"]=now();jp.write_text(json.dumps(D,indent=2,ensure_ascii=False)+"\n",encoding="utf-8");L.w(f"JSON: {jp}");L.w(f"LOG : {lp}");L.close();return 0
if __name__=="__main__":raise SystemExit(main())
