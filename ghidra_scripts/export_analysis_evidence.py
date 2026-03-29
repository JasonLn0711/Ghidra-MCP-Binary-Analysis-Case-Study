# Export Ghidra-derived evidence for the MCP analysis workflow.
#@category Analysis
#@runtime Jython

import json
import os
from ghidra.app.decompiler import DecompInterface, DecompileOptions
from ghidra.program.model.data import StringDataInstance
from ghidra.program.util import DefinedDataIterator
from util import CollectionUtils


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def to_hex(address):
    return "0x%s" % address.toString()


def get_functions():
    funcs = []
    fm = currentProgram.getFunctionManager()
    for func in fm.getFunctions(True):
        funcs.append({
            "name": func.getName(),
            "address": to_hex(func.getEntryPoint()),
        })
    return funcs


def decompile_function_by_name(name):
    func = getGlobalFunctions(name)
    if not func:
        return None

    interface = DecompInterface()
    options = DecompileOptions()
    interface.setOptions(options)
    interface.toggleSyntaxTree(False)
    interface.toggleCCode(True)

    try:
        if not interface.openProgram(currentProgram):
            raise RuntimeError("Decompiler failed to open program: %s" % interface.getLastMessage())
        result = interface.decompileFunction(func[0], 60, monitor)
        if not result.decompileCompleted():
            raise RuntimeError("Decompiler failed for %s: %s" % (name, result.getErrorMessage()))
        return result.getDecompiledFunction().getC()
    finally:
        interface.closeProgram()
        interface.dispose()


def interesting_string(text):
    patterns = [
        "Format:",
        "FLAG{",
        "HINT:",
        "Decoy:",
        "OK!",
        "Wrong key.",
        "mcp{",
        "GIZQgizumbcnxkW",
    ]
    for pattern in patterns:
        if pattern in text:
            return True
    return False


def collect_strings():
    out = []
    for data in CollectionUtils.asIterable(
        DefinedDataIterator.definedStrings(currentProgram, currentSelection)
    ):
        sdi = StringDataInstance.getStringDataInstance(data)
        value = sdi.getStringValue()
        if value and interesting_string(value):
            out.append({
                "address": to_hex(data.getAddress()),
                "value": value,
            })
    return out


def collect_xrefs(target_address):
    addr = toAddr(target_address)
    refs = []
    ref_iter = currentProgram.getReferenceManager().getReferencesTo(addr)
    while ref_iter.hasNext():
        ref = ref_iter.next()
        from_addr = ref.getFromAddress()
        func = getFunctionContaining(from_addr)
        refs.append({
            "from_address": to_hex(from_addr),
            "from_function": func.getName() if func else "<no function>",
            "type": str(ref.getReferenceType()),
        })
    return refs


def write_text(path, data):
    handle = open(path, "w")
    try:
        handle.write(data)
    finally:
        handle.close()


def main():
    args = getScriptArgs()
    if not args:
        raise RuntimeError("Expected output directory as first script argument")

    out_dir = args[0]
    ensure_dir(out_dir)

    functions = get_functions()
    strings = collect_strings()
    xrefs = {}
    for item in strings:
        xrefs[item["address"]] = collect_xrefs(item["address"])

    verify_format_c = decompile_function_by_name("verify_format")
    decode_expected_key_c = decompile_function_by_name("decode_expected_key")
    verify_key_c = decompile_function_by_name("verify_key")
    xor_decrypt_flag_c = decompile_function_by_name("xor_decrypt_flag")

    evidence = {
        "program_name": currentProgram.getName(),
        "functions": functions,
        "strings": strings,
        "xrefs": xrefs,
        "decompile": {
            "verify_format": verify_format_c,
            "decode_expected_key": decode_expected_key_c,
            "verify_key": verify_key_c,
            "xor_decrypt_flag": xor_decrypt_flag_c,
        },
    }

    write_text(
        os.path.join(out_dir, "functions_top30.txt"),
        "\n".join(
            ["%s  %s" % (entry["address"], entry["name"]) for entry in functions[:30]]
        ) + "\n"
    )
    write_text(os.path.join(out_dir, "verify_format.c"), verify_format_c or "")
    write_text(os.path.join(out_dir, "decode_expected_key.c"), decode_expected_key_c or "")
    write_text(os.path.join(out_dir, "verify_key.c"), verify_key_c or "")
    write_text(os.path.join(out_dir, "xor_decrypt_flag.c"), xor_decrypt_flag_c or "")
    write_text(os.path.join(out_dir, "evidence.json"), json.dumps(evidence, indent=2, sort_keys=True))


main()
