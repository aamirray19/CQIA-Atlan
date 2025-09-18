from pathlib import Path
from typing import List, Dict, Any
import ast
import esprima
import astor

class AgentPayloadBuilder:
    """
    Builds function/class-wise payloads. If parsing fails, it gracefully
    falls back to creating a single, file-level payload.
    """

    PY_EXT = {".py"}
    JS_EXT = {".js"}

    @staticmethod
    def build_payloads(files: List[Path]) -> List[Dict[str, Any]]:
        payloads = []

        for file_path in files:
            if not file_path.is_file():
                continue
            
            ext = file_path.suffix.lower()

            if ext not in AgentPayloadBuilder.PY_EXT and ext not in AgentPayloadBuilder.JS_EXT:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                payloads.append({
                    "file_path": str(file_path),
                    "error": f"Could not read file due to error: {type(e).__name__} - {str(e)}"
                })
                continue

            if ext in AgentPayloadBuilder.PY_EXT:
                payloads.extend(AgentPayloadBuilder._python_payload(file_path, content))

            elif ext in AgentPayloadBuilder.JS_EXT:
                payloads.extend(AgentPayloadBuilder._js_payload(file_path, content))

        return payloads

    @staticmethod
    def _create_file_fallback_payload(file_path: Path, code: str, error: str) -> Dict[str, Any]:
        """Creates a payload for the entire file when deep parsing fails."""
        return {
            "file_path": str(file_path),
            "type": "file",
            "name": file_path.name,
            "lines_of_code": len(code.splitlines()),
            "raw_code": code,
            "language": file_path.suffix.lower(),
            "parsing_error": error
        }


    # Python Payload builder 
    @staticmethod
    def _python_payload(file_path: Path, code: str) -> List[Dict[str, Any]]:
        try:
            tree = ast.parse(code)
            if hasattr(ast, 'fix_missing_locations'):
                ast.fix_missing_locations(tree)
        except Exception as e:
            error_message = f"Python parse error: {str(e)}"
            return [AgentPayloadBuilder._create_file_fallback_payload(file_path, code, error_message)]

        payloads = []
        
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                start_line = node.lineno
                end_line = getattr(node, 'end_lineno', start_line)
                
                raw_code = "\n".join(code.splitlines()[start_line - 1:end_line])

                node_type = "function"
                if isinstance(node, ast.ClassDef):
                    node_type = "class"
                elif isinstance(node, ast.AsyncFunctionDef):
                    node_type = "async_function"

                payloads.append({
                    "file_path": str(file_path),
                    "type": node_type,
                    "name": node.name,
                    "lines_of_code": end_line - start_line + 1,
                    "raw_code": raw_code,
                    "ast_dump": astor.dump_tree(node),
                    "language": ".py"
                })

        if not payloads and code.strip():
            payloads.append({
                "file_path": str(file_path),
                "type": "file",
                "name": file_path.name,
                "lines_of_code": len(code.splitlines()),
                "raw_code": code,
                "ast_dump": astor.dump_tree(tree),
                "language": ".py"
            })
            
        return payloads


    # JavaScript
    @staticmethod
    def _js_payload(file_path: Path, code: str) -> List[Dict[str, Any]]:
        try:
            tree = esprima.parseModule(code, options={'tolerant': True, 'loc': True, 'jsx': True})
        except Exception:
            try:
                tree = esprima.parseScript(code, options={'tolerant': True, 'loc': True, 'jsx': True})
            except Exception as e:
                error_message = f"JS parse error: {str(e)}"
                return [AgentPayloadBuilder._create_file_fallback_payload(file_path, code, error_message)]

        payloads = []
        for node in tree.body:
            node_type_str = ""
            node_name = "<anonymous>"
            
            if node.type in ["FunctionDeclaration", "ClassDeclaration"]:
                node_type_str = "function" if node.type == "FunctionDeclaration" else "class"
                if node.id:
                    node_name = node.id.name

            elif node.type == "VariableDeclaration":
                for declaration in node.declarations:
                    if declaration.init and declaration.init.type in ["ArrowFunctionExpression", "FunctionExpression"]:
                         node_type_str = "arrow_function_component"
                         if declaration.id:
                             node_name = declaration.id.name
            
            if node_type_str:
                start = node.loc.start.line
                end = node.loc.end.line
                raw_code = "\n".join(code.splitlines()[start - 1:end])
                payloads.append({
                    "file_path": str(file_path),
                    "type": node_type_str,
                    "name": node_name,
                    "lines_of_code": end - start + 1,
                    "raw_code": raw_code,
                    "language": ".js"
                })
        
        if not payloads and code.strip():
            payloads.append({
                "file_path": str(file_path),
                "type": "file",
                "name": file_path.name,
                "lines_of_code": len(code.splitlines()),
                "raw_code": code,
                "language": ".js"
            })
            
        return payloads