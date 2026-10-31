using System;
using System.IO;
using System.Linq;
using Mono.Cecil;
using Mono.Cecil.Cil;

namespace KolkataPatcher;

internal class Program
{
    private static void Main(string[] args)
    {
        Console.ForegroundColor = ConsoleColor.Cyan;
        Console.WriteLine("==========================================================");
        Console.WriteLine("    Scam With Your Friends - Kolkata OS Patcher & Bypass  ");
        Console.WriteLine("                 Open Source Edition (GPLv3)              ");
        Console.WriteLine("==========================================================");
        Console.ResetColor();
        Console.WriteLine();

        try
        {
            bool isInteractive = args.Length == 0;
            string managedDir = ResolveManagedDirectory(args);
            if (string.IsNullOrEmpty(managedDir) || !Directory.Exists(managedDir))
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("[-] Error: Could not locate the 'Managed' folder of the game.");
                Console.ResetColor();
                Console.WriteLine("    Please place KolkataPatcher in the game folder (next to the .exe),");
                Console.WriteLine("    or pass the game folder path as an argument.");
                WaitAndExit(1, isInteractive);
                return;
            }

            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine($"[+] Found Managed directory: {managedDir}");
            Console.ResetColor();

            if (args.Contains("--restore", StringComparer.OrdinalIgnoreCase))
            {
                RestoreBackups(managedDir);
                WaitAndExit(0, isInteractive);
                return;
            }

            Console.WriteLine();
            Console.WriteLine("Applying patches...");

            PatchCoreModule(managedDir);
            PatchUnityWebRequestModule(managedDir);
            PatchScriptsAssDef(managedDir);
            PatchAssemblyCSharp(managedDir);

            Console.WriteLine();
            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("==========================================================");
            Console.WriteLine("  [SUCCESS] All patches successfully applied!");
            Console.WriteLine("  - Functional PlayerPrefs engine restored (fixes Scamazon purchases, notification spam & camera)");
            Console.WriteLine("  - UnityWebRequest.Get(Uri) restored");
            Console.WriteLine("  - Kolkata OS Auth loop bypassed (SignedIn / Unlimited)");
            Console.WriteLine("  - Taskbar / CallerQueue UI crash fixed");
            Console.WriteLine("  - Piracy warning disabled");
            Console.WriteLine("  - Web browser privacy blocker bypassed (instant open)");
            Console.WriteLine("  - AI redirect: redirected to local proxy (http://127.0.0.1:8888)");
            Console.WriteLine("  - Host settings bypass: removed in-game key and model requirements");
            Console.WriteLine("==========================================================");
            Console.ResetColor();
            Console.WriteLine();
            Console.WriteLine("You can now launch the game via Steam / Proton / Windows directly!");
            WaitAndExit(0, isInteractive);
        }
        catch (Exception ex)
        {
            Console.ForegroundColor = ConsoleColor.Red;
            Console.WriteLine();
            Console.WriteLine($"[-] Fatal error while patching: {ex.Message}");
            Console.WriteLine(ex.StackTrace);
            Console.ResetColor();
            WaitAndExit(1, args.Length == 0);
            return;
        }
    }

    private static string ResolveManagedDirectory(string[] args)
    {
        var dirArg = args.FirstOrDefault(a => !a.StartsWith("--"));
        if (!string.IsNullOrEmpty(dirArg) && Directory.Exists(dirArg))
        {
            string p = dirArg;
            if (Path.GetFileName(p).Equals("Managed", StringComparison.OrdinalIgnoreCase)) return p;
            string subManaged = Path.Combine(p, "Scam With Your Friends_Data", "Managed");
            if (Directory.Exists(subManaged)) return subManaged;
            string altManaged = Path.Combine(p, "Managed");
            if (Directory.Exists(altManaged)) return altManaged;
        }

        string cur = AppDomain.CurrentDomain.BaseDirectory;
        string[] candidates = new[]
        {
            Path.Combine(cur, "Scam With Your Friends_Data", "Managed"),
            Path.Combine(cur, "Managed"),
            Path.Combine(cur, "Scam With Your Friends", "Scam With Your Friends_Data", "Managed"),
            Path.Combine(cur, "..", "Scam With Your Friends_Data", "Managed"),
            Path.Combine(cur, "..", "Managed")
        };

        foreach (var c in candidates)
        {
            if (Directory.Exists(c) && File.Exists(Path.Combine(c, "Assembly-CSharp.dll")))
            {
                return Path.GetFullPath(c);
            }
        }

        // Try interactive input
        Console.Write("Enter path to game folder or 'Managed' directory: ");
        string input = Console.ReadLine()?.Trim('"', ' ', '\'');
        if (!string.IsNullOrEmpty(input) && Directory.Exists(input))
        {
            if (Path.GetFileName(input).Equals("Managed", StringComparison.OrdinalIgnoreCase)) return input;
            string sub = Path.Combine(input, "Scam With Your Friends_Data", "Managed");
            if (Directory.Exists(sub)) return sub;
            string alt = Path.Combine(input, "Managed");
            if (Directory.Exists(alt)) return alt;
        }

        return null;
    }

    private static void EnsureBackup(string filePath)
    {
        string bakPath = filePath + ".bak";
        if (!File.Exists(bakPath))
        {
            File.Copy(filePath, bakPath, false);
            Console.ForegroundColor = ConsoleColor.DarkGray;
            Console.WriteLine($"    Created backup: {Path.GetFileName(bakPath)}");
            Console.ResetColor();
        }
    }

    private static void RestoreBackups(string managedDir)
    {
        Console.WriteLine("Restoring backups...");
        string[] files = new[] { "UnityEngine.CoreModule.dll", "UnityEngine.UnityWebRequestModule.dll", "ScriptsAssDef.dll", "Assembly-CSharp.dll" };
        foreach (var f in files)
        {
            string target = Path.Combine(managedDir, f);
            string bak = target + ".bak";
            if (File.Exists(bak))
            {
                File.Copy(bak, target, true);
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine($"[+] Restored {f} from backup");
                Console.ResetColor();
            }
            else
            {
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine($"[!] No backup found for {f}");
                Console.ResetColor();
            }
        }

        string swyfPrefs = Path.Combine(managedDir, "SWYF.Prefs.dll");
        if (File.Exists(swyfPrefs))
        {
            try
            {
                File.Delete(swyfPrefs);
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("[+] Removed SWYF.Prefs.dll");
                Console.ResetColor();
            }
            catch {}
        }

        Console.WriteLine("[+] Restore completed.");
    }

    private static void PatchCoreModule(string managedDir)
    {
        string path = Path.Combine(managedDir, "UnityEngine.CoreModule.dll");
        if (!File.Exists(path)) return;

        EnsureBackup(path);

        // Extract SWYF.Prefs.dll to managed directory
        string swyfPrefsPath = Path.Combine(managedDir, "SWYF.Prefs.dll");
        using (var stream = typeof(Program).Assembly.GetManifestResourceStream("KolkataPatcher.Resources.SWYF.Prefs.dll"))
        {
            if (stream != null)
            {
                using var fs = File.Create(swyfPrefsPath);
                stream.CopyTo(fs);
            }
            else
            {
                var resNames = typeof(Program).Assembly.GetManifestResourceNames();
                var match = resNames.FirstOrDefault(n => n.EndsWith("SWYF.Prefs.dll", StringComparison.OrdinalIgnoreCase));
                if (match != null)
                {
                    using var s = typeof(Program).Assembly.GetManifestResourceStream(match);
                    using var fs = File.Create(swyfPrefsPath);
                    s.CopyTo(fs);
                }
            }
        }

        var resolver = new DefaultAssemblyResolver();
        resolver.AddSearchDirectory(managedDir);
        var readerParams = new ReaderParameters { AssemblyResolver = resolver, ReadingMode = ReadingMode.Immediate };

        byte[] raw = File.ReadAllBytes(path);
        using var ms = new MemoryStream(raw);
        using var asm = AssemblyDefinition.ReadAssembly(ms, readerParams);

        var ppType = asm.MainModule.Types.FirstOrDefault(t => t.FullName == "UnityEngine.PlayerPrefs");
        if (ppType == null) return;

        var prefsAsm = resolver.Resolve(new AssemblyNameReference("SWYF.Prefs", new Version(1, 0, 0, 0)));
        var swyfPrefsType = prefsAsm.MainModule.Types.FirstOrDefault(t => t.FullName == "UnityEngine.SwyfPlayerPrefs");
        if (swyfPrefsType == null) return;

        var voidType = asm.MainModule.TypeSystem.Void;
        var stringType = asm.MainModule.TypeSystem.String;
        var intType = asm.MainModule.TypeSystem.Int32;
        var floatType = asm.MainModule.TypeSystem.Single;
        var boolType = asm.MainModule.TypeSystem.Boolean;

        bool modified = false;

        void RedirectMethod(string name, TypeReference returnType, params TypeReference[] paramTypes)
        {
            var targetMethod = swyfPrefsType.Methods.FirstOrDefault(m => m.Name == name && m.Parameters.Count == paramTypes.Length);
            if (targetMethod == null) return;

            var targetMethodRef = asm.MainModule.ImportReference(targetMethod);

            var existing = ppType.Methods.FirstOrDefault(m => m.Name == name && m.Parameters.Count == paramTypes.Length);
            MethodDefinition method;
            if (existing != null)
            {
                method = existing;
                method.Body.Instructions.Clear();
                method.Body.Variables.Clear();
                method.Body.ExceptionHandlers.Clear();
            }
            else
            {
                method = new MethodDefinition(name, MethodAttributes.Public | MethodAttributes.Static | MethodAttributes.HideBySig, returnType);
                for (int i = 0; i < paramTypes.Length; i++)
                {
                    method.Parameters.Add(new ParameterDefinition("arg" + i, ParameterAttributes.None, paramTypes[i]));
                }
                ppType.Methods.Add(method);
            }

            var il = method.Body.GetILProcessor();
            for (int i = 0; i < paramTypes.Length; i++)
            {
                if (i == 0) il.Emit(OpCodes.Ldarg_0);
                else if (i == 1) il.Emit(OpCodes.Ldarg_1);
                else if (i == 2) il.Emit(OpCodes.Ldarg_2);
                else il.Emit(OpCodes.Ldarg, i);
            }
            il.Emit(OpCodes.Call, targetMethodRef);
            il.Emit(OpCodes.Ret);
            modified = true;
        }

        RedirectMethod("SetInt", voidType, stringType, intType);
        RedirectMethod("GetInt", intType, stringType, intType);
        RedirectMethod("GetInt", intType, stringType);
        RedirectMethod("SetFloat", voidType, stringType, floatType);
        RedirectMethod("GetFloat", floatType, stringType, floatType);
        RedirectMethod("GetFloat", floatType, stringType);
        RedirectMethod("SetString", voidType, stringType, stringType);
        RedirectMethod("GetString", stringType, stringType, stringType);
        RedirectMethod("GetString", stringType, stringType);
        RedirectMethod("HasKey", boolType, stringType);
        RedirectMethod("DeleteKey", voidType, stringType);
        RedirectMethod("DeleteAll", voidType);
        RedirectMethod("Save", voidType);

        if (modified)
        {
            asm.Write(path + ".tmp");
            File.Move(path + ".tmp", path, true);
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("[*] Patched UnityEngine.CoreModule.dll (restored full functional PlayerPrefs engine)");
            Console.ResetColor();
        }
        else
        {
            Console.WriteLine("[ ] UnityEngine.CoreModule.dll already patched");
        }
    }

    private static void PatchUnityWebRequestModule(string managedDir)
    {
        string path = Path.Combine(managedDir, "UnityEngine.UnityWebRequestModule.dll");
        if (!File.Exists(path)) return;

        EnsureBackup(path);

        var resolver = new DefaultAssemblyResolver();
        resolver.AddSearchDirectory(managedDir);
        var readerParams = new ReaderParameters { AssemblyResolver = resolver, ReadingMode = ReadingMode.Immediate };

        byte[] raw = File.ReadAllBytes(path);
        using var ms = new MemoryStream(raw);
        using var asm = AssemblyDefinition.ReadAssembly(ms, readerParams);

        var uwrType = asm.MainModule.Types.FirstOrDefault(t => t.FullName == "UnityEngine.Networking.UnityWebRequest");
        if (uwrType == null) return;

        if (!uwrType.Methods.Any(m => m.Name == "Get" && m.Parameters.Count == 1 && m.Parameters[0].ParameterType.FullName == "System.Uri"))
        {
            var uriType = asm.MainModule.ImportReference(typeof(Uri));
            var getStringMethod = uwrType.Methods.FirstOrDefault(m => m.Name == "Get" && m.Parameters.Count == 1 && m.Parameters[0].ParameterType.FullName == "System.String");
            if (getStringMethod != null)
            {
                var method = new MethodDefinition("Get", MethodAttributes.Public | MethodAttributes.Static | MethodAttributes.HideBySig, uwrType);
                method.Parameters.Add(new ParameterDefinition("uri", ParameterAttributes.None, uriType));
                var il = method.Body.GetILProcessor();
                var getAbsoluteUri = asm.MainModule.ImportReference(typeof(Uri).GetProperty("AbsoluteUri")?.GetGetMethod());
                il.Emit(OpCodes.Ldarg_0);
                il.Emit(OpCodes.Callvirt, getAbsoluteUri);
                il.Emit(OpCodes.Call, getStringMethod);
                il.Emit(OpCodes.Ret);
                uwrType.Methods.Add(method);

                asm.Write(path + ".tmp");
                File.Move(path + ".tmp", path, true);
                Console.ForegroundColor = ConsoleColor.Cyan;
                Console.WriteLine("[*] Patched UnityEngine.UnityWebRequestModule.dll (restored UnityWebRequest.Get(Uri))");
                Console.ResetColor();
                return;
            }
        }

        Console.WriteLine("[ ] UnityEngine.UnityWebRequestModule.dll already patched");
    }

    private static void PatchScriptsAssDef(string managedDir)
    {
        string path = Path.Combine(managedDir, "ScriptsAssDef.dll");
        if (!File.Exists(path)) return;

        EnsureBackup(path);

        var resolver = new DefaultAssemblyResolver();
        resolver.AddSearchDirectory(managedDir);
        var readerParams = new ReaderParameters { AssemblyResolver = resolver, ReadingMode = ReadingMode.Immediate };

        byte[] raw = File.ReadAllBytes(path);
        using var ms = new MemoryStream(raw);
        using var asm = AssemblyDefinition.ReadAssembly(ms, readerParams);

        var hostAi = asm.MainModule.Types.FirstOrDefault(t => t.Name == "HostAiSettings");
        if (hostAi == null) return;

        bool modified = false;

        var openRouterProp = hostAi.Properties.FirstOrDefault(p => p.Name == "OpenRouterSelected");
        if (openRouterProp?.GetMethod != null)
        {
            var m = openRouterProp.GetMethod;
            m.Body.Instructions.Clear();
            m.Body.Variables.Clear();
            m.Body.ExceptionHandlers.Clear();
            var il = m.Body.GetILProcessor();
            il.Emit(OpCodes.Ldc_I4_1);
            il.Emit(OpCodes.Ret);
            modified = true;
        }

        var directProp = hostAi.Properties.FirstOrDefault(p => p.Name == "UseDirectOpenRouter");
        if (directProp?.GetMethod != null)
        {
            var m = directProp.GetMethod;
            m.Body.Instructions.Clear();
            m.Body.Variables.Clear();
            m.Body.ExceptionHandlers.Clear();
            var il = m.Body.GetILProcessor();
            il.Emit(OpCodes.Ldc_I4_1);
            il.Emit(OpCodes.Ret);
            modified = true;
        }

        if (modified)
        {
            asm.Write(path + ".tmp");
            File.Move(path + ".tmp", path, true);
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("[*] Patched ScriptsAssDef.dll (forced OpenRouter / Gateway backend)");
            Console.ResetColor();
        }
        else
        {
            Console.WriteLine("[ ] ScriptsAssDef.dll already patched");
        }
    }

    private static void PatchAssemblyCSharp(string managedDir)
    {
        string path = Path.Combine(managedDir, "Assembly-CSharp.dll");
        if (!File.Exists(path)) return;

        EnsureBackup(path);

        var resolver = new DefaultAssemblyResolver();
        resolver.AddSearchDirectory(managedDir);
        var readerParams = new ReaderParameters { AssemblyResolver = resolver, ReadingMode = ReadingMode.Immediate };

        byte[] raw = File.ReadAllBytes(path);
        using var ms = new MemoryStream(raw);
        using var asm = AssemblyDefinition.ReadAssembly(ms, readerParams);

        var apiType = asm.MainModule.Types.FirstOrDefault(t => t.Name == "KolkataApi");
        var queueAppType = asm.MainModule.Types.FirstOrDefault(t => t.FullName == "Kolkata.UI.KolkataOsCallerQueueApp");

        if (apiType == null || queueAppType == null) return;

        var uniTaskAsm = resolver.Resolve(new AssemblyNameReference("UniTask", null));
        var uniTaskDef = uniTaskAsm.MainModule.Types.First(t => t.FullName == "Cysharp.Threading.Tasks.UniTask");

        var jsonAsm = resolver.Resolve(new AssemblyNameReference("Newtonsoft.Json", null));
        var jObjectDef = jsonAsm.MainModule.Types.First(t => t.FullName == "Newtonsoft.Json.Linq.JObject");

        var systemAsm = resolver.Resolve(new AssemblyNameReference("System", null));
        var stopwatchDef = systemAsm.MainModule.Types.First(t => t.FullName == "System.Diagnostics.Stopwatch");

        var jObjectParse = asm.MainModule.ImportReference(jObjectDef.Methods.First(m => m.Name == "Parse" && m.Parameters.Count == 1));
        var fromResultGeneric = uniTaskDef.Methods.First(m => m.Name == "FromResult" && m.GenericParameters.Count == 1);
        var fromResultJObject = asm.MainModule.ImportReference(new GenericInstanceMethod(fromResultGeneric) { GenericArguments = { asm.MainModule.ImportReference(jObjectDef) } });
        var completedTaskField = asm.MainModule.ImportReference(uniTaskDef.Fields.First(f => f.Name == "CompletedTask"));
        var restartMethod = asm.MainModule.ImportReference(stopwatchDef.Methods.First(m => m.Name == "Restart" && m.Parameters.Count == 0));

        // 1. Fix null workshop-page button crash in KolkataOsCallerQueueApp.BuildContent
        var buildContentMethod = queueAppType.Methods.FirstOrDefault(m => m.Name == "BuildContent");
        if (buildContentMethod != null)
        {
            var instrs = buildContentMethod.Body.Instructions;
            for (int i = 0; i < instrs.Count - 5; i++)
            {
                if (instrs[i].OpCode == OpCodes.Ldstr && (string)instrs[i].Operand == "workshop-page")
                {
                    int startIdx = i - 2;
                    int endIdx = i + 6;
                    for (int j = startIdx; j <= endIdx; j++)
                    {
                        instrs[j].OpCode = OpCodes.Nop;
                        instrs[j].Operand = null;
                    }
                    Console.ForegroundColor = ConsoleColor.Cyan;
                    Console.WriteLine("[*] Fixed KolkataOsCallerQueueApp.BuildContent (prevented null workshop-page crash)");
                    Console.ResetColor();
                    break;
                }
            }
        }

        // 2. Patch EnsureEdgeSessionAsync in KolkataApi
        var ensureMethod = apiType.Methods.First(m => m.Name == "EnsureEdgeSessionAsync");
        ensureMethod.Body.Instructions.Clear();
        ensureMethod.Body.Variables.Clear();
        ensureMethod.Body.ExceptionHandlers.Clear();
        var il = ensureMethod.Body.GetILProcessor();

        void SetField(string name, OpCode loadOp, object val)
        {
            var f = apiType.Fields.FirstOrDefault(x => x.Name == name);
            if (f == null) return;
            il.Emit(OpCodes.Ldarg_0);
            if (loadOp == OpCodes.Ldc_I4) il.Emit(loadOp, (int)val);
            else if (loadOp == OpCodes.Ldc_I8) il.Emit(loadOp, (long)val);
            else if (loadOp == OpCodes.Ldstr) il.Emit(loadOp, (string)val);
            il.Emit(OpCodes.Stfld, f);
        }

        void SetProp(string name, OpCode loadOp, object val)
        {
            var p = apiType.Properties.FirstOrDefault(x => x.Name == name);
            if (p?.SetMethod == null) return;
            il.Emit(OpCodes.Ldarg_0);
            if (loadOp == OpCodes.Ldc_I4) il.Emit(loadOp, (int)val);
            else if (loadOp == OpCodes.Ldc_I8) il.Emit(loadOp, (long)val);
            else if (loadOp == OpCodes.Ldstr) il.Emit(loadOp, (string)val);
            il.Emit(OpCodes.Callvirt, p.SetMethod);
        }

        SetField("edgeAuthStatus", OpCodes.Ldc_I4, 2); // SignedIn
        SetField("edgeSessionValidated", OpCodes.Ldc_I4, 1);
        SetField("edgeOwnershipMissing", OpCodes.Ldc_I4, 0);
        SetField("edgeStatusLoaded", OpCodes.Ldc_I4, 1);
        SetField("browserRecoveryAvailable", OpCodes.Ldc_I4, 0);
        SetField("browserRecoveryFailed", OpCodes.Ldc_I4, 0);
        SetField("edgeAuthenticationFailures", OpCodes.Ldc_I4, 0);
        SetField("edgeSessionExpires", OpCodes.Ldc_I8, 2147483647L);
        SetField("edgeAiExpires", OpCodes.Ldc_I8, 2147483647L);
        SetField("edgeAiRefreshAt", OpCodes.Ldc_I8, 2147483647L);
        SetField("edgeServerTime", OpCodes.Ldc_I8, 1792618285L);
        SetField("edgeSession", OpCodes.Ldstr, "bypassed_session_token");
        SetField("edgeAi", OpCodes.Ldstr, "bypassed_ai_token");

        var swField = apiType.Fields.FirstOrDefault(x => x.Name == "edgeServerElapsed");
        if (swField != null)
        {
            il.Emit(OpCodes.Ldarg_0);
            il.Emit(OpCodes.Ldfld, swField);
            il.Emit(OpCodes.Callvirt, restartMethod);
        }

        SetProp("MembershipRole", OpCodes.Ldc_I4, 3); // Unlimited
        SetProp("AiCreditsDepleted", OpCodes.Ldc_I4, 0);
        SetProp("DiscordBonusClaimed", OpCodes.Ldc_I4, 1);
        SetProp("DiscordVipState", OpCodes.Ldstr, "verified");
        SetProp("HasDiscordVip", OpCodes.Ldc_I4, 1);
        SetProp("AiBanned", OpCodes.Ldc_I4, 0);
        SetProp("AiUsageRestricted", OpCodes.Ldc_I4, 0);

        il.Emit(OpCodes.Ldsfld, completedTaskField);
        il.Emit(OpCodes.Ret);
        Console.ForegroundColor = ConsoleColor.Cyan;
        Console.WriteLine("[*] Patched EnsureEdgeSessionAsync (session set to SignedIn / Unlimited)");
        Console.ResetColor();

        // 3. Patch EdgePostAsync
        var edgePostMethod = apiType.Methods.First(m => m.Name == "EdgePostAsync");
        edgePostMethod.Body.Instructions.Clear();
        edgePostMethod.Body.Variables.Clear();
        edgePostMethod.Body.ExceptionHandlers.Clear();
        var epIl = edgePostMethod.Body.GetILProcessor();
        epIl.Emit(OpCodes.Ldstr, "{\"token\":\"bypassed_token\",\"role\":\"unlimited\",\"status\":\"active\",\"success\":true,\"credits_available\":true,\"discord_bonus_claimed\":true,\"discord_vip\":true,\"discord_vip_status\":\"verified\",\"vip_valid_until\":2147483647,\"recheck_after\":300,\"ownsapp\":true,\"appid\":\"4954910\"}");
        epIl.Emit(OpCodes.Call, jObjectParse);
        epIl.Emit(OpCodes.Call, fromResultJObject);
        epIl.Emit(OpCodes.Ret);
        Console.ForegroundColor = ConsoleColor.Cyan;
        Console.WriteLine("[*] Patched EdgePostAsync (returning valid mock auth JSON)");
        Console.ResetColor();

        // 4. Patch EdgeLimitsAsync
        var limitsMethod = apiType.Methods.First(m => m.Name == "EdgeLimitsAsync");
        limitsMethod.Body.Instructions.Clear();
        limitsMethod.Body.Variables.Clear();
        limitsMethod.Body.ExceptionHandlers.Clear();
        var limIl = limitsMethod.Body.GetILProcessor();
        limIl.Emit(OpCodes.Ldstr, "{\"max_prompt_tokens\":128000,\"max_context_tokens\":128000,\"max_output_tokens\":4096,\"success\":true}");
        limIl.Emit(OpCodes.Call, jObjectParse);
        limIl.Emit(OpCodes.Call, fromResultJObject);
        limIl.Emit(OpCodes.Ret);
        Console.ForegroundColor = ConsoleColor.Cyan;
        Console.WriteLine("[*] Patched EdgeLimitsAsync (mock limits)");
        Console.ResetColor();

        // 4b. Patch ResolveEdgePromptAsync (mock prompt bundle so game never queries kolkata-ai.jataterworldwide.com)
        var resolveMethod = apiType.Methods.FirstOrDefault(m => m.Name == "ResolveEdgePromptAsync");
        if (resolveMethod != null)
        {
            resolveMethod.Body.Instructions.Clear();
            resolveMethod.Body.Variables.Clear();
            resolveMethod.Body.ExceptionHandlers.Clear();
            var rIl = resolveMethod.Body.GetILProcessor();
            rIl.Emit(OpCodes.Ldstr, "{\"prompt_version\":\"v1\",\"system_prompt\":\"\",\"response_format\":{\"type\":\"json_object\"},\"limits\":{\"max_prompt_tokens\":128000,\"max_context_tokens\":128000,\"max_output_tokens\":4096,\"success\":true}}");
            rIl.Emit(OpCodes.Call, jObjectParse);
            rIl.Emit(OpCodes.Call, fromResultJObject);
            rIl.Emit(OpCodes.Ret);
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("[*] Patched ResolveEdgePromptAsync (offline mock prompt version)");
            Console.ResetColor();
        }

        // 4c. Patch EdgeBase (force all API routes to local gateway)
        var edgeBaseMethod = apiType.Methods.FirstOrDefault(m => m.Name == "EdgeBase");
        if (edgeBaseMethod != null)
        {
            edgeBaseMethod.Body.Instructions.Clear();
            edgeBaseMethod.Body.Variables.Clear();
            edgeBaseMethod.Body.ExceptionHandlers.Clear();
            var ebIl = edgeBaseMethod.Body.GetILProcessor();
            ebIl.Emit(OpCodes.Ldstr, "http://127.0.0.1:8888");
            ebIl.Emit(OpCodes.Ret);
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("[*] Patched EdgeBase (redirected backend base URL to http://127.0.0.1:8888)");
            Console.ResetColor();
        }

        // 5. Patch ShouldShowPiracyWarning
        var piracyMethod = apiType.Methods.First(m => m.Name == "ShouldShowPiracyWarning");
        piracyMethod.Body.Instructions.Clear();
        piracyMethod.Body.Variables.Clear();
        piracyMethod.Body.ExceptionHandlers.Clear();
        var pirIl = piracyMethod.Body.GetILProcessor();
        pirIl.Emit(OpCodes.Ldc_I4_0);
        pirIl.Emit(OpCodes.Ret);
        Console.ForegroundColor = ConsoleColor.Cyan;
        Console.WriteLine("[*] Patched ShouldShowPiracyWarning (disabled alarm)");
        Console.ResetColor();

        // 6. Patch Browser Privacy in KolkataOsController and KolkataOsBrowserHost
        var osControllerType = asm.MainModule.Types.FirstOrDefault(t => t.FullName == "Kolkata.UI.KolkataOsController");
        if (osControllerType != null)
        {
            var reqPrivacyMethod = osControllerType.Methods.FirstOrDefault(m => m.Name == "RequestBrowserPrivacyWarning");
            if (reqPrivacyMethod != null)
            {
                reqPrivacyMethod.Body.Instructions.Clear();
                reqPrivacyMethod.Body.Variables.Clear();
                reqPrivacyMethod.Body.ExceptionHandlers.Clear();
                var rIl = reqPrivacyMethod.Body.GetILProcessor();
                rIl.Emit(OpCodes.Ldc_I4_0); // return false -> bypass modal, open directly
                rIl.Emit(OpCodes.Ret);
                Console.ForegroundColor = ConsoleColor.Cyan;
                Console.WriteLine("[*] Patched RequestBrowserPrivacyWarning (browser opens directly without consent modal)");
                Console.ResetColor();
            }
        }

        var browserHostType = asm.MainModule.Types.FirstOrDefault(t => t.FullName == "Kolkata.UI.KolkataOsBrowserHost");
        if (browserHostType != null)
        {
            var approveMethod = browserHostType.Methods.FirstOrDefault(m => m.Name == "ApproveOpening");
            var privField = browserHostType.Fields.FirstOrDefault(f => f.Name == "privacyApproved");
            if (approveMethod != null && privField != null)
            {
                approveMethod.Body.Instructions.Clear();
                approveMethod.Body.Variables.Clear();
                approveMethod.Body.ExceptionHandlers.Clear();
                var aIl = approveMethod.Body.GetILProcessor();
                aIl.Emit(OpCodes.Ldarg_0);
                aIl.Emit(OpCodes.Ldc_I4_1);
                aIl.Emit(OpCodes.Stfld, privField);
                aIl.Emit(OpCodes.Ret);
            }

            var ensureBrowserMethod = browserHostType.Methods.FirstOrDefault(m => m.Name == "EnsureBrowserClient");
            if (ensureBrowserMethod != null && ensureBrowserMethod.Body.Instructions.Count >= 6)
            {
                for (int i = 0; i <= 5; i++)
                {
                    ensureBrowserMethod.Body.Instructions[i].OpCode = OpCodes.Nop;
                    ensureBrowserMethod.Body.Instructions[i].Operand = null;
                }
                Console.ForegroundColor = ConsoleColor.Cyan;
                Console.WriteLine("[*] Patched KolkataOsBrowserHost (bypassed privacy approval check for CEF/UWB)");
                Console.ResetColor();
            }
        }

        // 7. Patch CompleteOpenRouterAsync: Redirect to Local Proxy & remove in-game model/key checks
        var completeAsyncType = apiType.NestedTypes.FirstOrDefault(t => t.Name.Contains("CompleteOpenRouterAsync"))
                             ?? asm.MainModule.Types.FirstOrDefault(t => t.Name.Contains("<CompleteOpenRouterAsync>"));
        if (completeAsyncType != null)
        {
            var moveNextMethod = completeAsyncType.Methods.FirstOrDefault(m => m.Name == "MoveNext");
            if (moveNextMethod != null)
            {
                var instrs = moveNextMethod.Body.Instructions;
                for (int i = 0; i < instrs.Count; i++)
                {
                    // Redirect endpoint string to local proxy
                    if (instrs[i].OpCode == OpCodes.Ldstr && 
                        ((string)instrs[i].Operand == "https://openrouter.ai/api/v1/chat/completions" ||
                         (string)instrs[i].Operand == "https://inference.celeris.ai/celeris-1/v1/chat/completions"))
                    {
                        instrs[i].Operand = "http://127.0.0.1:8888/v1/chat/completions";
                        Console.ForegroundColor = ConsoleColor.Cyan;
                        Console.WriteLine("[*] Patched CompleteOpenRouterAsync endpoint -> http://127.0.0.1:8888/v1/chat/completions");
                        Console.ResetColor();
                    }

                    // NOP out the brfalse check on UseDirectOpenRouter so it NEVER branches to CompleteEdgeForCallerAsync
                    if (instrs[i].OpCode == OpCodes.Call && instrs[i].Operand is MethodReference mr && mr.Name == "get_UseDirectOpenRouter")
                    {
                        if (i + 1 < instrs.Count && (instrs[i + 1].OpCode == OpCodes.Brfalse || instrs[i + 1].OpCode == OpCodes.Brfalse_S))
                        {
                            instrs[i + 1].OpCode = OpCodes.Nop;
                            instrs[i + 1].Operand = null;
                            Console.ForegroundColor = ConsoleColor.Cyan;
                            Console.WriteLine("[*] Bypassed UseDirectOpenRouter fallback branch in CompleteOpenRouterAsync");
                            Console.ResetColor();
                        }
                    }

                    // Bypass "Paste an OpenRouter API key in Host Settings"
                    if (instrs[i].OpCode == OpCodes.Ldstr && (string)instrs[i].Operand == "Paste an OpenRouter API key in Host Settings.")
                    {
                        for (int k = i; k < i + 20 && k < instrs.Count; k++)
                        {
                            if (instrs[k].OpCode == OpCodes.Throw)
                            {
                                for (int j = i - 2; j <= k; j++)
                                {
                                    instrs[j].OpCode = OpCodes.Nop;
                                    instrs[j].Operand = null;
                                }
                                Console.ForegroundColor = ConsoleColor.Cyan;
                                Console.WriteLine("[*] Removed 'Paste an OpenRouter API key' error throw");
                                Console.ResetColor();
                                break;
                            }
                        }
                    }

                    // Bypass "Choose an OpenRouter model in Host Settings."
                    if (instrs[i].OpCode == OpCodes.Ldstr && (string)instrs[i].Operand == "Choose an OpenRouter model in Host Settings.")
                    {
                        for (int k = i; k < i + 20 && k < instrs.Count; k++)
                        {
                            if (instrs[k].OpCode == OpCodes.Throw)
                            {
                                for (int j = i - 6; j <= k; j++)
                                {
                                    instrs[j].OpCode = OpCodes.Nop;
                                    instrs[j].Operand = null;
                                }
                                Console.ForegroundColor = ConsoleColor.Cyan;
                                Console.WriteLine("[*] Removed 'Choose an OpenRouter model' error throw");
                                Console.ResetColor();
                                break;
                            }
                        }
                    }
                }
            }
        }

        // Remove any System.Private.CoreLib reference if present
        var badRef = asm.MainModule.AssemblyReferences.FirstOrDefault(r => r.Name == "System.Private.CoreLib");
        if (badRef != null)
        {
            asm.MainModule.AssemblyReferences.Remove(badRef);
        }

        asm.Write(path + ".tmp");
        File.Move(path + ".tmp", path, true);
        Console.ForegroundColor = ConsoleColor.Green;
        Console.WriteLine("[+] Successfully wrote patched Assembly-CSharp.dll");
        Console.ResetColor();
    }

    private static void WaitAndExit(int code, bool interactive = true)
    {
        if (interactive && Environment.UserInteractive && !Console.IsInputRedirected)
        {
            Console.WriteLine();
            Console.WriteLine("Press any key to exit...");
            try { Console.ReadKey(true); } catch { }
        }
        Environment.Exit(code);
    }
}
