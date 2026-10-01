export class LiveConversation {
 constructor(hooks){this.hooks=hooks;this.closed=false;this.sources=new Set();this.next=0;this.cancelled=new Set();}
 send(data){if(this.socket?.readyState===WebSocket.OPEN)this.socket.send(JSON.stringify(data));}
 async connect(mode){
  try{
   this.media=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:true}});
   if(this.closed){this.media.getTracks().forEach(t=>t.stop());return;}
   const response=await fetch('/api/live',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode})});
   const data=await response.json();if(!response.ok)throw Error(data.error);
   if(this.closed)return;
   this.ctx=new AudioContext();await this.ctx.resume();await this.ctx.audioWorklet.addModule('/capture.js');
   if(this.closed)return;
   this.gain=this.ctx.createGain();this.gain.connect(this.ctx.destination);
   this.input=this.ctx.createMediaStreamSource(this.media);this.capture=new AudioWorkletNode(this.ctx,'capture');
   this.input.connect(this.capture);this.silence=this.ctx.createGain();this.silence.gain.value=0;this.capture.connect(this.silence).connect(this.ctx.destination);
   this.capture.port.onmessage=e=>{
    if(!this.ready||this.closed)return;
    const {pcm,audioEndTime,lastVoiceTime}=e.data,now=performance.now();
    if(this.captureClockOrigin===undefined)this.captureClockOrigin=now-this.ctx.currentTime*1000;
    const clockOrigin=this.captureClockOrigin;
    if(this.streamStartedAt===undefined)this.streamStartedAt=clockOrigin+audioEndTime*1000-pcm.byteLength/32;
    if(lastVoiceTime!==null){
     const at=clockOrigin+lastVoiceTime*1000;
     if(this.lastVoiceAudioTime===undefined||lastVoiceTime>this.lastVoiceAudioTime){
      if(!this.serverVadAvailable&&(this.lastVoiceAudioTime===undefined||lastVoiceTime-this.lastVoiceAudioTime>=.5)){this.firstSpeechReported=false;this.serverVoiceEndAt=undefined;this.hooks.questionStart?.();}
      this.lastVoiceAudioTime=lastVoiceTime;this.lastVoiceAt=at;this.localEndReported=false;
     }
     if(!this.localEndReported&&now-at>=500&&!this.firstSpeechReported){this.localEndReported=true;this.hooks.questionEnd?.(at,'microphone');}
    }
    const bytes=new Uint8Array(pcm);let s='';for(const b of bytes)s+=String.fromCharCode(b);
    this.send({realtimeInput:{audio:{data:btoa(s),mimeType:'audio/pcm;rate=16000'}}});
   };
   const socket=new WebSocket('wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContentConstrained?access_token='+encodeURIComponent(data.token));this.socket=socket;
   await new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>{reject(Error('Live connection timed out.'));this.close();},25000);
    socket.onopen=()=>this.send({setup:{model:'models/'+data.model,generationConfig:{responseModalities:['AUDIO']},systemInstruction:{parts:[{text:data.prompt}]},inputAudioTranscription:{},outputAudioTranscription:{},tools:[{functionDeclarations:data.tools}]}});
    socket.onmessage=async event=>{
     try{
      const message=JSON.parse(typeof event.data==='string'?event.data:await event.data.text());if(this.closed)return;
      if(message.setupComplete){clearTimeout(timer);this.ready=true;this.hooks.status('Listening');resolve();}
      if(message.error){clearTimeout(timer);throw Error(message.error.message||'Live API error');}
      for(const id of message.toolCallCancellation?.ids||[])this.cancelled.add(id);
      const usage=message.usageMetadata;if(usage)this.hooks.metrics?.({inputTokens:usage.promptTokenCount??usage.inputTokenCount,outputTokens:usage.responseTokenCount??usage.candidatesTokenCount});
      const sc=message.serverContent;
      const activity=message.voiceActivity;
      if(activity)this.serverVadAvailable=true;
      const activityType=activity?.type??activity?.voiceActivityType;
      if(activityType==='ACTIVITY_START'){
       this.firstSpeechReported=false;this.serverVoiceEndAt=undefined;this.hooks.questionStart?.();
      }
      if(activityType==='ACTIVITY_END'){
       const offset=Number.parseFloat(activity.audioOffset);
       this.serverVoiceEndAt=Number.isFinite(offset)&&this.streamStartedAt!==undefined?this.streamStartedAt+offset*1000:undefined;
       const at=this.serverVoiceEndAt??this.lastVoiceAt;
       if(at!==undefined&&!this.firstSpeechReported)this.hooks.questionEnd?.(at,this.serverVoiceEndAt!==undefined?'server VAD':'microphone');
      }
      if(sc?.interrupted){this.stopAudio();this.hooks.interrupted();this.hooks.status('Listening');}
      if(sc?.inputTranscription?.text)this.hooks.input(sc.inputTranscription.text);
      if(sc?.outputTranscription?.text){this.turnHasOutput=true;this.hooks.output(sc.outputTranscription.text);}
      for(const part of sc?.modelTurn?.parts||[])if(part.inlineData?.data)this.play(part.inlineData.data,Number(/rate=(\d+)/.exec(part.inlineData.mimeType)?.[1])||24000);
      for(const call of message.toolCall?.functionCalls||[]){
       this.hooks.status('Querying database');let result;
       try{const r=await fetch('/api/tool',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode,name:call.name,args:call.args||{}})});result=await r.json();}catch{result={error:'Database tool unavailable'};}
       if(this.closed||this.cancelled.has(call.id))continue;
       this.hooks.tool({name:call.name,args:call.args||{},result});
       this.send({toolResponse:{functionResponses:[{id:call.id,name:call.name,response:result}]}});
      }
      if(sc?.turnComplete){if(this.turnHasOutput){this.hooks.complete();this.turnHasOutput=false;}if(this.sources.size===0)this.hooks.status('Listening');}
     }catch(error){clearTimeout(timer);this.hooks.error(error.message);reject(error);this.close();}
    };
    socket.onerror=()=>{clearTimeout(timer);reject(Error('Could not connect to Gemini Live 3.8.'));};
    socket.onclose=event=>{clearTimeout(timer);if(!this.closed){const msg=event.reason||'Live disconnected. Start talking to reconnect.';this.hooks.error(msg);reject(Error(msg));this.close();}};
   });
  }catch(error){this.close();throw error;}
 }
 play(base64,rate){
  if(!this.ctx||this.closed)return;const bytes=Uint8Array.from(atob(base64),c=>c.charCodeAt(0));const pcm=new Int16Array(bytes.buffer);
  if(!pcm.length)return;
  const buffer=this.ctx.createBuffer(1,pcm.length,rate);buffer.getChannelData(0).set(Float32Array.from(pcm,n=>n/32768));
  const source=this.ctx.createBufferSource();source.buffer=buffer;source.connect(this.gain);const start=Math.max(this.ctx.currentTime,this.next);this.next=start+buffer.duration;this.sources.add(source);
  this.hooks.status('Speaking');source.onended=()=>{this.sources.delete(source);if(this.sources.size===0&&!this.closed)this.hooks.status('Listening');};source.start(start);
  const firstSample=pcm.findIndex(value=>Math.abs(value)>64);
  if(firstSample>=0&&!this.firstSpeechReported){
   this.firstSpeechReported=true;
   const audioTime=start+firstSample/rate,stamp=this.ctx.getOutputTimestamp?.();
   const speechAt=stamp?.performanceTime>0?stamp.performanceTime+(audioTime-stamp.contextTime)*1000:performance.now()+Math.max(0,audioTime-this.ctx.currentTime)*1000+(this.ctx.outputLatency||this.ctx.baseLatency||0)*1000;
   const questionEnd=this.serverVoiceEndAt??this.lastVoiceAt;
   this.hooks.firstReply?.({at:speechAt,questionEnd,elapsedMs:questionEnd!==undefined&&speechAt>=questionEnd?speechAt-questionEnd:undefined,source:this.serverVoiceEndAt!==undefined?'server VAD':'microphone'});
  }
 }
 stopAudio(){for(const source of this.sources){try{source.stop();}catch{}}this.sources.clear();this.next=this.ctx?.currentTime||0;}
 close(){this.closed=true;this.ready=false;this.stopAudio();this.capture?.disconnect();this.input?.disconnect();this.media?.getTracks().forEach(t=>t.stop());this.socket?.close();void this.ctx?.close();}
}
