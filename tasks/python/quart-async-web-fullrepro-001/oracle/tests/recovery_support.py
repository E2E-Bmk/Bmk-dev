from __future__ import annotations
from dataclasses import replace
import importlib
from pathlib import Path
from typing import Any, Callable

def qwf() -> Any: return importlib.import_module("quart_workflow")
def expect(error: type[BaseException], call: Callable[[], Any]) -> BaseException:
    try: call()
    except error as exc: return exc
    raise AssertionError("expected " + error.__name__)

def atomic_case(root: str, tmp: Path) -> None:
    w=qwf()
    if root=="A09":
        x=w.LifespanSupervisor(tmp); r=x.open("app",("config","db"),("db","config"),owner="a",operation_id="op"); r=x.started(r,"config"); expect(w.TransitionError,lambda:x.started(r,"config")); assert x.recover("op",owner="a")==r
    elif root=="A10":
        x=w.LifespanSupervisor(tmp); r=x.open("app",("config","db"),("db","config"),owner="a",operation_id="op"); r=x.started(r,"config"); r=x.fail(r,"db"); r=x.stopped(r,"config"); assert r.state=="closed" and w.value(r,"failure")=="db"
    elif root=="A11":
        x=w.ContextBroker(tmp); r=x.open("r","request","task-a",owner="a",operation_id="op"); assert x.assert_task(r,"task-a"); expect(w.OwnershipError,lambda:x.assert_task(r,"task-b"))
    elif root=="A12":
        x=w.ContextBroker(tmp); old=x.open("r","websocket","task-a",owner="a",operation_id="op"); new=x.handoff(old,"task-b",new_owner="b",operation_id="move"); expect(w.ConflictError,lambda:x.close(old,task_id="task-a")); assert x.close(new,task_id="task-b").owner=="b"
    elif root=="A13":
        x=w.StreamChannel(tmp); r=x.open("s",1,owner="a",operation_id="op"); r=x.send(r,b"one"); expect(w.TransitionError,lambda:x.send(r,b"two")); r=x.acknowledge(r); r=x.send(r,b"two"); r=x.cancel(r); assert x.close(r).state=="closed"
    elif root=="A14":
        x=w.ASGITranscript(tmp); r=x.open("x","http",owner="a",operation_id="op"); r=x.receive(r,{"type":"http.request"}); expect(w.TransitionError,lambda:x.send(r,{"type":"http.response.body"})); r=x.send(r,{"type":"http.response.start"}); r=x.send(r,{"type":"http.response.body"}); assert x.close(r).state=="closed"
    elif root=="A15":
        x=w.SessionCoordinator(tmp); r=x.open("sid",0,owner="a",operation_id="op"); r=x.set(r,"cart",[1,2]); r=x.commit(r); expect(w.ConflictError,lambda:x.open("sid",0,owner="b",operation_id="stale")); assert dict(r.payload)["values"]=={"cart":[1,2]}
    elif root=="A16":
        x=w.BlueprintRouter(tmp); r=x.register("api","/v1",{"/items":("GET","POST")},{404:"missing"},owner="a",operation_id="op"); assert x.resolve(r,"POST","/v1/items")==("api","/items") and x.error_handler(r,404)=="missing"; expect(KeyError,lambda:x.resolve(r,"DELETE","/v1/items"))
    else: raise KeyError(root)

def integration_case(root: str, tmp: Path) -> None:
    w=qwf(); life=w.LifespanSupervisor(tmp/"l"); ctx=w.ContextBroker(tmp/"c"); stream=w.StreamChannel(tmp/"s"); asgi=w.ASGITranscript(tmp/"a"); session=w.SessionCoordinator(tmp/"n"); router=w.BlueprintRouter(tmp/"r")
    if root=="I05":
        r=life.open("app",("config","db"),("db","config"),owner="a",operation_id="l"); r=life.started(r,"config"); r=life.fail(r,"boom"); r=life.stopped(r,"config"); e=asgi.open("life","lifespan",owner="a",operation_id="a"); e=asgi.receive(e,{"type":"lifespan.startup"}); e=asgi.send(e,{"type":"lifespan.startup.failed"}); assert r.state=="closed" and e.state=="sending"
    elif root=="I06":
        r=life.open("app",("config","db"),("db","config"),owner="a",operation_id="l"); r=life.started(r,"config"); r=life.started(r,"db"); e=asgi.open("life","lifespan",owner="a",operation_id="a"); e=asgi.receive(e,{"type":"lifespan.shutdown"}); e=asgi.send(e,{"type":"lifespan.shutdown.complete"}); r=life.stopped(r,"db"); r=life.stopped(r,"config"); assert r.state=="closed" and e.history[-1]=="sending"
    elif root=="I07":
        a=ctx.open("app","app","task",owner="a",operation_id="a"); r=ctx.open("req","request","task",owner="a",operation_id="r",parent=a.digest); assert w.value(r,"parent")==a.digest and ctx.close(r,task_id="task").state=="closed" and ctx.verify(a)
    elif root=="I08":
        r=ctx.open("ws","websocket","listen",owner="a",operation_id="c"); r=ctx.handoff(r,"worker",new_owner="b",operation_id="m"); expect(w.OwnershipError,lambda:ctx.assert_task(r,"listen")); assert ctx.close(r,task_id="worker").state=="closed"
    elif root=="I09":
        c=ctx.open("req","request","task",owner="a",operation_id="c"); s=stream.open("body",1,owner="a",operation_id="s"); s=stream.send(s,b"a"); expect(w.TransitionError,lambda:stream.close(s)); s=stream.acknowledge(s); assert stream.close(s).state=="closed" and ctx.assert_task(c,"task")
    elif root=="I10":
        s=stream.open("body",2,owner="a",operation_id="s"); s=stream.send(s,b"a"); s=stream.send(s,b"b"); s=stream.cancel(s); s=stream.close(s); e=asgi.open("x","http",owner="a",operation_id="a"); e=asgi.receive(e,{"type":"http.disconnect"}); assert s.state=="closed" and w.value(e,"terminal")
    elif root=="I11":
        e=asgi.open("x","http",owner="a",operation_id="a"); e=asgi.receive(e,{"type":"http.request"}); e=asgi.send(e,{"type":"http.response.start"}); e=asgi.send(e,{"type":"http.response.body","more_body":True}); s=stream.open("out",1,owner="a",operation_id="s"); s=stream.send(s,b"p"); expect(w.TransitionError,lambda:stream.send(s,b"n")); assert not w.value(e,"terminal")
    elif root=="I12":
        e=asgi.open("x","websocket",owner="a",operation_id="a"); e=asgi.receive(e,{"type":"websocket.connect"}); e=asgi.send(e,{"type":"websocket.accept"}); e=asgi.send(e,{"type":"websocket.close"}); c=ctx.open("ws","websocket","task",owner="a",operation_id="c"); assert asgi.close(e).state==ctx.close(c,task_id="task").state=="closed"
    elif root=="I13":
        n=session.open("sid",0,owner="a",operation_id="n"); n=session.set(n,"x",1); n=session.rollback(n); e=asgi.open("x","http",owner="a",operation_id="a"); e=asgi.receive(e,{"type":"http.disconnect"}); assert dict(n.payload)["values"]=={} and w.value(e,"terminal")
    elif root=="I14":
        b=router.register("api","/api",{"/bad":("GET",)},{500:"bp-error"},owner="a",operation_id="b"); e=asgi.open("x","http",owner="a",operation_id="a"); assert router.resolve(b,"GET","/api/bad")==("api","/bad") and router.error_handler(b,500)=="bp-error" and e.owner=="a"
    elif root=="I15":
        b=router.register("api","/api",{"/item":("POST",)},{409:"conflict"},owner="a",operation_id="b"); n=session.open("sid",0,owner="a",operation_id="n"); n=session.set(n,"route",router.resolve(b,"POST","/api/item")[1]); n=session.commit(n); assert dict(n.payload)["values"]["route"]=="/item"
    elif root=="I16":
        c=ctx.open("r","request","a",owner="a",operation_id="c"); n=session.open("sid",0,owner="a",operation_id="n"); m=ctx.handoff(c,"b",new_owner="b",operation_id="m"); expect(w.ConflictError,lambda:ctx.close(c,task_id="a")); assert session.rollback(n).state=="rolled_back" and m.owner=="b"
    elif root=="I17":
        l=life.open("app",("config","db"),("db","config"),owner="a",operation_id="l"); l=life.started(l,"config"); l=life.started(l,"db"); c=ctx.open("app","app","task",owner="a",operation_id="c"); c=ctx.close(c,task_id="task"); l=life.stopped(l,"db"); l=life.stopped(l,"config"); assert c.state==l.state=="closed"
    elif root=="I18":
        l=life.open("app",("config","db"),("db","config"),owner="a",operation_id="l"); l=life.started(l,"config"); l=life.fail(l,"db"); l=life.stopped(l,"config"); n=session.open("sid",0,owner="a",operation_id="n"); assert l.state=="closed" and session.rollback(n).state=="rolled_back"
    elif root=="I19":
        b=router.register("api","/api",{"/stream":("GET",)},{500:"stream-error"},owner="a",operation_id="b"); s=stream.open("s",1,owner="a",operation_id="s"); s=stream.send(s,b"one"); expect(w.TransitionError,lambda:stream.send(s,b"two")); assert router.error_handler(b,500)=="stream-error"
    elif root=="I20":
        e=asgi.open("x","http",owner="a",operation_id="a"); e=asgi.receive(e,{"type":"http.request"}); e=asgi.send(e,{"type":"http.response.start"}); e=asgi.send(e,{"type":"http.response.body"}); n=session.open("sid",0,owner="a",operation_id="n"); n=session.set(n,"status",200); n=session.commit(n); assert asgi.close(e).state=="closed" and n.state=="committed"
    elif root=="I21":
        c=ctx.open("r","request","task",owner="a",operation_id="c"); e=asgi.open("x","http",owner="a",operation_id="a"); e=asgi.receive(e,{"type":"http.disconnect"}); expect(w.TransitionError,lambda:asgi.receive(e,{"type":"http.request"})); assert ctx.close(c,task_id="task").state=="closed"
    elif root=="I22":
        s=stream.open("s",1,owner="a",operation_id="s"); s=stream.send(s,b"one"); bad=replace(s,digest="0"*64); expect(w.IntegrityError,lambda:stream.verify(bad)); expect(w.IntegrityError,lambda:stream.close(bad)); assert stream.current("s")==s
    elif root=="I23":
        old=router.register("api","/v1",{"/x":("GET",)},{404:"v1"},owner="a",operation_id="one"); new=router.register("api","/v2",{"/x":("GET",)},{404:"v2"},owner="a",operation_id="two"); expect(w.IntegrityError,lambda:router.resolve(old,"GET","/v1/x")); assert router.resolve(new,"GET","/v2/x")==("api","/x")
    elif root=="I24":
        c=ctx.open("r","request","a",owner="a",operation_id="c"); c=ctx.handoff(c,"b",new_owner="b",operation_id="m"); e=asgi.open("x","http",owner="b",operation_id="a"); e=asgi.receive(e,{"type":"http.request"}); assert c.owner==e.owner and ctx.assert_task(c,"b")
    else: raise KeyError(root)

def system_case(root: str, tmp: Path) -> None:
    w=qwf(); flow=w.QuartWorkflow(tmp); parts=flow.begin("run",owner="alice",operation_id="w1")
    if root=="S03":
        done=flow.succeed(parts,b"ok"); assert flow.verify(done) and {r.state for r in done.values()}>={"closed","committed","registered"}
    elif root=="S04":
        l=flow.lifespans.started(parts["life"],"config"); l=flow.lifespans.fail(l,"service"); l=flow.lifespans.stopped(l,"config"); s=flow.streams.cancel(parts["stream"]); s=flow.streams.close(s); n=flow.sessions.rollback(parts["session"]); assert l.state==s.state=="closed" and n.state=="rolled_back"
    elif root=="S05":
        c=flow.contexts.handoff(parts["context"],"task-2",new_owner="bob",operation_id="move"); expect(w.ConflictError,lambda:flow.contexts.close(parts["context"],task_id="task-1")); e=flow.exchanges.receive(parts["exchange"],{"type":"http.disconnect"}); assert c.owner=="bob" and w.value(e,"terminal")
    elif root=="S06":
        done=flow.succeed(parts,b"one"); reopened=w.QuartWorkflow(tmp); names={"life":"lifespans","context":"contexts","stream":"streams","exchange":"exchanges","session":"sessions","blueprint":"blueprints"}; recovered={k:getattr(reopened,names[k]).recover(v.operation_id,owner=v.owner) for k,v in done.items()}; assert reopened.verify(recovered) and recovered==done
    elif root=="S07":
        e=flow.exchanges.receive(parts["exchange"],{"type":"http.request"}); e=flow.exchanges.send(e,{"type":"http.response.start"}); s=flow.streams.send(parts["stream"],b"partial"); reopened=w.QuartWorkflow(tmp); e=reopened.exchanges.send(reopened.exchanges.recover(e.operation_id,owner="alice"),{"type":"http.response.body"}); s=reopened.streams.acknowledge(reopened.streams.recover(s.operation_id,owner="alice")); assert reopened.exchanges.close(e).state==reopened.streams.close(s).state=="closed"
    elif root=="S08":
        done=flow.succeed(parts,b"ok"); bad={**done,"stream":replace(done["stream"],digest=done["exchange"].digest)}; expect(w.IntegrityError,lambda:flow.verify(bad)); assert flow.verify(done)
    else: raise KeyError(root)
