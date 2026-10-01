class Capture extends AudioWorkletProcessor {
 constructor(){super();this.buffer=[];this.position=0;this.lastVoiceTime=null;}
 process(inputs){
  const input=inputs[0]?.[0];if(!input)return true;
  const audioEndTime=currentTime+input.length/sampleRate;
  const rms=Math.sqrt(input.reduce((sum,value)=>sum+value*value,0)/input.length);
  if(rms>.008)this.lastVoiceTime=audioEndTime;
  const ratio=sampleRate/16000;
  while(this.position<input.length){
   const i=Math.floor(this.position),f=this.position-i;
   const value=input[i]*(1-f)+(input[Math.min(i+1,input.length-1)]??input[i])*f;
   this.buffer.push(Math.max(-32768,Math.min(32767,Math.round(value*32767))));
   this.position+=ratio;
  }
  this.position-=input.length;
  if(this.buffer.length>=1600){const pcm=new Int16Array(this.buffer.splice(0,1600));this.port.postMessage({pcm:pcm.buffer,audioEndTime,lastVoiceTime:this.lastVoiceTime},[pcm.buffer]);}
  return true;
 }
}
registerProcessor('capture',Capture);
