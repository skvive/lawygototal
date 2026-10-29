/** LAWYGO CMS -> existing native Supabase boards, audited server-to-server ingestion.
 * Deploy only with an approved tenant and a secret unique to this service.
 */
import { NextRequest, NextResponse } from "next/server";
import { timingSafeEqual } from "node:crypto";
import { getSupabaseAdmin } from "@/lib/supabaseClient";
import { resolveBoardBySlug } from "@/lib/boardService";

export const runtime = "nodejs";
const MODULE_BOARD = {channel:"lawygo_channel",wiki:"lawygo_wiki",pan:"lawygo_pan"} as const;
const ID_RE = /^[a-f0-9]{32}$/i;

type Incoming = {
 source:string; source_id:string; product:keyof typeof MODULE_BOARD;
 revision:number; title:string; body:string; author:string; sponsored:boolean;
 action?:"upsert"|"delete";
};
function fail(code:number,error:string){return NextResponse.json({error},{status:code});}
function allowed(request:NextRequest){
 const expected=process.env.LAWYGO_NATIVE_BRIDGE_SECRET ?? "";
 const actual=(request.headers.get("authorization") ?? "").replace(/^Bearer /i,"");
 if(expected.length<32 || !actual || actual.length!==expected.length) return false;
 return timingSafeEqual(Buffer.from(actual),Buffer.from(expected));
}
function escapeHTML(value:string){
 return value.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
 .replace(/"/g,"&quot;").replace(/'/g,"&#39;");
}
export async function POST(req:NextRequest){
 if(!allowed(req))return fail(401,"인증되지 않은 서비스입니다.");
 const tenant=(process.env.LAWYGO_NATIVE_MANAGEMENT_NUMBER ?? "").trim();
 if(!tenant)return fail(503,"운영 게시판 관리번호가 설정되지 않았습니다.");
 const db=getSupabaseAdmin();
 if(!db)return fail(503,"Supabase DB가 연결되지 않았습니다.");
 let body:Incoming;
 try{body=await req.json();}catch{return fail(400,"잘못된 JSON입니다.");}
 if(!body || typeof body!=="object")return fail(400,"요청 객체가 없습니다.");
 if(body.source!=="lawygo-cms" || !ID_RE.test(body.source_id??"") ||
   !Object.prototype.hasOwnProperty.call(MODULE_BOARD,body.product) ||
   !Number.isSafeInteger(body.revision) || body.revision<1 || body.revision>1000000 ||
   !["upsert","delete",undefined].includes(body.action) ||
   typeof body.title!=="string" || body.title.length<2 || body.title.length>180 ||
   typeof body.body!=="string" || body.body.length>40000 ||
   typeof body.sponsored!=="boolean") return fail(422,"검증되지 않은 콘텐츠입니다.");
 const source=`cms:${body.source_id}`;
 try{
   const board=await resolveBoardBySlug(MODULE_BOARD[body.product],tenant);
   if(!board || board.managementNumber!==tenant) return fail(503,"전용 네이티브 게시판이 준비되지 않았습니다.");
   const {data:old,error:readError}=await db.from("board_posts").select("id,num_id,board_id,cms_external_revision,deleted_at")
     .eq("management_number",tenant).eq("cms_external_source",source).maybeSingle();
   if(readError)throw readError;
   if(old && Number(old.cms_external_revision)>=body.revision)
      return NextResponse.json({ok:true,unchanged:true,postId:old.num_id});
   if(body.action==="delete"){
      if(!old)return NextResponse.json({ok:true,unchanged:true});
      const {error}=await db.from("board_posts").update({deleted_at:new Date().toISOString(),cms_external_revision:body.revision})
        .eq("id",old.id).eq("management_number",tenant);
      if(error)throw error;
      return NextResponse.json({ok:true,deleted:true,postId:old.num_id});
   }
   const values={
      board_id:board.id,management_number:tenant,
      title:escapeHTML(body.title.trim()),content:escapeHTML(body.body.trim()),
      category:body.sponsored?"광고 · 콘텐츠":"전문 콘텐츠",author_name:"LAWYGO CMS",
      author_login_id:"lawygo_cms_service",cms_external_source:source,
      cms_external_revision:body.revision,deleted_at:null,updated_at:new Date().toISOString(),
   };
   if(old){
      // Keep board association for already migrated entries.
      const {data,error}=await db.from("board_posts").update({...values,board_id:old.board_id})
        .eq("id",old.id).eq("management_number",tenant).lt("cms_external_revision",body.revision)
        .select("num_id").maybeSingle();
      if(error)throw error;
      if(!data)return NextResponse.json({ok:true,unchanged:true,postId:old.num_id});
      return NextResponse.json({ok:true,updated:true,postId:data.num_id});
   }
   const {data,error}=await db.from("board_posts").insert(values).select("num_id").single();
   if(error){
      // Concurrent duplicate insert will be rejected by the unique index; caller can safely retry.
      if(error.code==="23505")return fail(409,"동시 등록 충돌입니다. 다시 동기화해 주세요.");
      throw error;
   }
   return NextResponse.json({ok:true,created:true,postId:data.num_id});
 }catch(e){
   console.error("[LAWYGO CMS Bridge] native insert failed",e instanceof Error?e.name:"Error");
   return fail(502,"운영 게시판에 반영하지 못했습니다. 서버 로그를 확인해 주세요.");
 }
}
