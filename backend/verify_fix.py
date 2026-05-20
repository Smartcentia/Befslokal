import asyncio,sys,os,traceback
from app.services.tools.contract_tools import search_contracts
sys.path.append(os.getcwd())
async def main():
 try:
  print("START")
  print(await search_contracts("parkering"))
  print("SUCCESS")
 except:
  traceback.print_exc()
if __name__=="__main__": asyncio.run(main())
