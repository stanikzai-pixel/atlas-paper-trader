"""CLI: python main.py smoke | run | render.
Smoke is offline; run uses public READ-ONLY endpoints, no exchange account.
"""
import argparse,sys,time,traceback
from src import engine,site

STATE='data/state.json'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['smoke','run','render'])
    args=parser.parse_args()
    state=engine.load(STATE)
    if args.mode=='smoke':
        import unittest
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests'))
        site.render(state)
        return 0 if result.wasSuccessful() else 1
    if args.mode=='render':
        site.render(state)
        return 0
    now=int(time.time()*1000)
    try:
        result=engine.live_tick(state,now)
        engine.save(STATE,result)
        site.render(result)
        print('ENGINE OK:',result['status'],'provider:',result['provider'],'trades:',len(result['trades']))
        if result.get('warnings'):print('WARNINGS:',result['warnings'])
        return 0
    except Exception as exc:
        # Fail closed: do NOT generate an entry, simulated fill or price from a failed API.
        state['status']='ERROR'
        state['last_checked']=engine.utc(now)
        state['last_error']=f'{type(exc).__name__}: {str(exc)[:330]}'
        state['warnings']=['Market feed or validation failed; trading paused, previous state preserved']
        engine.save(STATE,state)
        site.render(state)
        print('::error:: Atlas feed failed; dashboard shows ERROR. '+state['last_error'])
        return 0  # workflow stays able to publish ERROR dashboard; never pretends it traded.

if __name__=='__main__':sys.exit(main())
