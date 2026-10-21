const grpc = require('/usr/src/app/node_modules/@grpc/grpc-js');
const loader = require('/usr/src/app/node_modules/@grpc/proto-loader');
const proto = grpc.loadPackageDefinition(loader.loadSync('/usr/src/app/demo.proto'));
const client = new proto.oteldemo.PaymentService('127.0.0.1:50051', grpc.credentials.createInsecure());
const sleep = ms => new Promise(r => setTimeout(r, ms));
const count = Number(process.argv[2] || 6);
(async () => {
 let success = 0, failures = 0;
 for (let i=0;i<count;i++) {
  const now=new Date();
  const current=i%2===0;
  const request={amount:{units:25,nanos:0,currencyCode:'USD'},creditCard:{creditCardNumber:'4111111111111111',creditCardCvv:123,creditCardExpirationMonth:now.getUTCMonth()+1,creditCardExpirationYear:now.getUTCFullYear()+(current?0:1)}};
  const result=await new Promise(resolve=>client.charge(request,{deadline:Date.now()+10000},(err,res)=>resolve(err?{ok:false,message:err.details}:{ok:true})));
  if(result.ok)success++;else failures++;
  console.log(JSON.stringify({time:new Date().toISOString(),case:current?'current-month':'future-year',...result}));
  if(count>10)await sleep(2000);
 }
 console.log(JSON.stringify({success,failures}));client.close();
})().catch(e=>{console.error(e.message);process.exitCode=1;client.close()});
