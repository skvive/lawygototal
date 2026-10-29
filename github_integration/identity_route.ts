/** Native LAWYGO site_users lookup for the verified Google subject from CMS.
 * Server-to-server only. The client must independently verify Google's ID token first.
 */
import { NextRequest,NextResponse } from 'next/server';
import { timingSafeEqual } from 'node:crypto';
import { getSupabaseAdmin } from '@/lib/supabaseClient';
import { isLoginAllowedStatus } from '@/lib/userAdmin';
export const runtime='nodejs';
function authorized(req:NextRequest){
  const key=process.env.LAWYGO_NATIVE_BRIDGE_SECRET??'';
  const token=(req.headers.get('authorization')??'').replace(/^Bearer /i,'');
  return key.length>=32&&token.length===key.length&&timingSafeEqual(Buffer.from(key),Buffer.from(token));
}
export async function POST(request:NextRequest){
  if(!authorized(request))return NextResponse.json({error:'unauthorized'},{status:401});
  let payload:unknown;try{payload=await request.json()}catch{return NextResponse.json({error:'invalid json'},{status:400})}
  if(!payload||typeof payload!=='object'||!('googleSub' in payload)||typeof payload.googleSub!=='string'||payload.googleSub.length<2||payload.googleSub.length>200){
    return NextResponse.json({error:'invalid google sub'},{status:400});
  }
  const db=getSupabaseAdmin();if(!db)return NextResponse.json({error:'database unavailable'},{status:503});
  const {data,error}=await db.from('site_users').select('id,google_id,status,management_number').eq('google_id',payload.googleSub).maybeSingle();
  if(error)return NextResponse.json({error:'lookup failure'},{status:503});
  if(!data||!isLoginAllowedStatus(data.status)||!data.management_number){
    return NextResponse.json({error:'membership not active'},{status:404});
  }
  return NextResponse.json({active:true,id:String(data.id),tenant:String(data.management_number)},
    {headers:{'Cache-Control':'private, no-store'}});
}
