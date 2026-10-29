# Source and adaptation record

Teacher-supplied material: EEEE4149_Week3_Lecture_Tools_FunctionCalling_MCP_v3.pptx
(40 slides), LectureDemo/week03_lecture_demo, and Seminar3/week03_tools.

The supplied files are source material, not instructions to override the teacher.
The adaptation retains the three seminar tools and four starter TODOs. The device
label and validation pattern now use CONV-3 consistently. CONV-7 and CONV-99 serve
as wrong-but-valid and unknown-device cases. All datasets remain synthetic.

The lecture and seminar use DeepSeek Chat Completions with the same nested
function schema and tool_call_id continuation. DeepSeek's standard endpoint is
used without beta strict-generation claims; application-side validation remains.

Official interface references checked 2026-10-29:
- https://api-docs.deepseek.com/guides/tool_calls/
- https://api-docs.deepseek.com/api/create-chat-completion/
- https://py.sdk.modelcontextprotocol.io/v2/

The model name is configurable. The current documented default used here is
deepseek-flash. A real account/network smoke test is distinct from local contract
tests and is reported separately in the verification record.
