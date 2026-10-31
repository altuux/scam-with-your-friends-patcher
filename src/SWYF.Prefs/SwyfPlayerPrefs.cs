using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;

namespace UnityEngine
{
    public static class SwyfPlayerPrefs
    {
        private static readonly Dictionary<string, int> s_ints = new Dictionary<string, int>(StringComparer.Ordinal);
        private static readonly Dictionary<string, float> s_floats = new Dictionary<string, float>(StringComparer.Ordinal);
        private static readonly Dictionary<string, string> s_strings = new Dictionary<string, string>(StringComparer.Ordinal);
        private static readonly object s_lock = new object();
        private static bool s_loaded = false;

        private const string RegistrySubKey = @"Software\Jatater Worldwide\Scam With Your Friends";

        private static string GetFilePath()
        {
            try
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                if (!string.IsNullOrEmpty(baseDir) && Directory.Exists(baseDir))
                {
                    return Path.Combine(baseDir, "swyf_playerprefs.dat");
                }
            }
            catch {}

            try
            {
                string appData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
                if (!string.IsNullOrEmpty(appData))
                {
                    string dir = Path.Combine(appData, "Scam With Your Friends");
                    Directory.CreateDirectory(dir);
                    return Path.Combine(dir, "swyf_playerprefs.dat");
                }
            }
            catch {}

            return "swyf_playerprefs.dat";
        }

        public static void EnsureLoaded()
        {
            lock (s_lock)
            {
                if (s_loaded) return;
                s_loaded = true;

                string path = GetFilePath();
                if (File.Exists(path))
                {
                    try
                    {
                        string[] lines = File.ReadAllLines(path);
                        foreach (string line in lines)
                        {
                            if (string.IsNullOrWhiteSpace(line) || line.Length < 3 || line[1] != ':') continue;
                            char type = line[0];
                            int eq = line.IndexOf('=', 2);
                            if (eq == -1) continue;

                            string keyB64 = line.Substring(2, eq - 2);
                            string val = line.Substring(eq + 1);

                            string key;
                            try
                            {
                                key = Encoding.UTF8.GetString(Convert.FromBase64String(keyB64));
                            }
                            catch
                            {
                                continue;
                            }

                            if (type == 'i')
                            {
                                if (int.TryParse(val, NumberStyles.Integer, CultureInfo.InvariantCulture, out int iVal))
                                    s_ints[key] = iVal;
                            }
                            else if (type == 'f')
                            {
                                if (float.TryParse(val, NumberStyles.Float, CultureInfo.InvariantCulture, out float fVal))
                                    s_floats[key] = fVal;
                            }
                            else if (type == 's')
                            {
                                try
                                {
                                    s_strings[key] = Encoding.UTF8.GetString(Convert.FromBase64String(val));
                                }
                                catch
                                {
                                    s_strings[key] = val;
                                }
                            }
                        }
                        return;
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine("[SWYF-Prefs] Load failed: " + ex.Message);
                    }
                }

                // If file doesn't exist yet, attempt migration from Windows Registry via reflection
                try
                {
                    Type regType = Type.GetType("Microsoft.Win32.Registry, mscorlib");
                    if (regType != null)
                    {
                        PropertyInfo currentUserProp = regType.GetProperty("CurrentUser", BindingFlags.Public | BindingFlags.Static);
                        object currentUser = currentUserProp?.GetValue(null, null);
                        if (currentUser != null)
                        {
                            MethodInfo openSubKey = currentUser.GetType().GetMethod("OpenSubKey", new[] { typeof(string) });
                            object keyObj = openSubKey?.Invoke(currentUser, new object[] { RegistrySubKey });
                            if (keyObj is IDisposable dispKey)
                            {
                                using (dispKey)
                                {
                                    MethodInfo getValueNames = keyObj.GetType().GetMethod("GetValueNames", Type.EmptyTypes);
                                    MethodInfo getValue = keyObj.GetType().GetMethod("GetValue", new[] { typeof(string) });
                                    string[] names = getValueNames?.Invoke(keyObj, null) as string[];
                                    if (names != null)
                                    {
                                        foreach (var valName in names)
                                        {
                                            if (string.IsNullOrEmpty(valName)) continue;
                                            object raw = getValue?.Invoke(keyObj, new object[] { valName });
                                            if (raw == null) continue;

                                            string cleanKey = valName;
                                            int hashIdx = valName.LastIndexOf("_h", StringComparison.Ordinal);
                                            if (hashIdx > 0 && hashIdx < valName.Length - 2)
                                            {
                                                bool isHexOrDigits = true;
                                                for (int idx = hashIdx + 2; idx < valName.Length; idx++)
                                                {
                                                    char c = valName[idx];
                                                    if (!char.IsDigit(c) && (c < 'a' || c > 'f') && (c < 'A' || c > 'F'))
                                                    {
                                                        isHexOrDigits = false;
                                                        break;
                                                    }
                                                }
                                                if (isHexOrDigits) cleanKey = valName.Substring(0, hashIdx);
                                            }

                                            if (raw is int intVal)
                                            {
                                                s_ints[cleanKey] = intVal;
                                            }
                                            else if (raw is string strVal)
                                            {
                                                s_strings[cleanKey] = strVal;
                                            }
                                            else if (raw is byte[] byteVal)
                                            {
                                                try
                                                {
                                                    s_strings[cleanKey] = Encoding.UTF8.GetString(byteVal).TrimEnd('\0');
                                                }
                                                catch {}
                                            }
                                        }
                                        SaveInternal();
                                    }
                                }
                            }
                        }
                    }
                }
                catch {}
            }
        }

        private static void SaveInternal()
        {
            try
            {
                string path = GetFilePath();
                var lines = new List<string>(s_ints.Count + s_floats.Count + s_strings.Count);

                foreach (var kvp in s_ints)
                {
                    string k = Convert.ToBase64String(Encoding.UTF8.GetBytes(kvp.Key));
                    lines.Add("i:" + k + "=" + kvp.Value.ToString(CultureInfo.InvariantCulture));
                }

                foreach (var kvp in s_floats)
                {
                    string k = Convert.ToBase64String(Encoding.UTF8.GetBytes(kvp.Key));
                    lines.Add("f:" + k + "=" + kvp.Value.ToString(CultureInfo.InvariantCulture));
                }

                foreach (var kvp in s_strings)
                {
                    string k = Convert.ToBase64String(Encoding.UTF8.GetBytes(kvp.Key));
                    string v = Convert.ToBase64String(Encoding.UTF8.GetBytes(kvp.Value ?? string.Empty));
                    lines.Add("s:" + k + "=" + v);
                }

                File.WriteAllLines(path, lines);
            }
            catch (Exception ex)
            {
                Console.WriteLine("[SWYF-Prefs] Save failed: " + ex.Message);
            }
        }

        public static void Save()
        {
            lock (s_lock)
            {
                EnsureLoaded();
                SaveInternal();
            }
        }

        public static void SetInt(string key, int value)
        {
            if (string.IsNullOrEmpty(key)) return;
            lock (s_lock)
            {
                EnsureLoaded();
                s_ints[key] = value;
                SaveInternal();
            }
        }

        public static int GetInt(string key, int defaultValue)
        {
            if (string.IsNullOrEmpty(key)) return defaultValue;
            lock (s_lock)
            {
                EnsureLoaded();
                if (s_ints.TryGetValue(key, out int value)) return value;
                return defaultValue;
            }
        }

        public static int GetInt(string key)
        {
            return GetInt(key, 0);
        }

        public static void SetFloat(string key, float value)
        {
            if (string.IsNullOrEmpty(key)) return;
            lock (s_lock)
            {
                EnsureLoaded();
                s_floats[key] = value;
                SaveInternal();
            }
        }

        public static float GetFloat(string key, float defaultValue)
        {
            if (string.IsNullOrEmpty(key)) return defaultValue;
            lock (s_lock)
            {
                EnsureLoaded();
                if (s_floats.TryGetValue(key, out float value)) return value;
                return defaultValue;
            }
        }

        public static float GetFloat(string key)
        {
            return GetFloat(key, 0f);
        }

        public static void SetString(string key, string value)
        {
            if (string.IsNullOrEmpty(key)) return;
            lock (s_lock)
            {
                EnsureLoaded();
                s_strings[key] = value ?? string.Empty;
                SaveInternal();
            }
        }

        public static string GetString(string key, string defaultValue)
        {
            if (string.IsNullOrEmpty(key)) return defaultValue;
            lock (s_lock)
            {
                EnsureLoaded();
                if (s_strings.TryGetValue(key, out string value)) return value;
                return defaultValue;
            }
        }

        public static string GetString(string key)
        {
            return GetString(key, string.Empty);
        }

        public static bool HasKey(string key)
        {
            if (string.IsNullOrEmpty(key)) return false;
            lock (s_lock)
            {
                EnsureLoaded();
                return s_ints.ContainsKey(key) || s_floats.ContainsKey(key) || s_strings.ContainsKey(key);
            }
        }

        public static void DeleteKey(string key)
        {
            if (string.IsNullOrEmpty(key)) return;
            lock (s_lock)
            {
                EnsureLoaded();
                s_ints.Remove(key);
                s_floats.Remove(key);
                s_strings.Remove(key);
                SaveInternal();
            }
        }

        public static void DeleteAll()
        {
            lock (s_lock)
            {
                EnsureLoaded();
                s_ints.Clear();
                s_floats.Clear();
                s_strings.Clear();
                SaveInternal();
            }
        }
    }
}
