import os
file_path = r'c:\Users\USER\Desktop\CHF JOINED DATA\frontend\index.html'
with open(file_path, 'r') as f:
    content = f.read()

login_states = """function App() {
            // Login states
            const [isLoggedIn, setIsLoggedIn] = useState(localStorage.getItem("isLoggedIn") === "true");
            const [loginUsername, setLoginUsername] = useState("");
            const [loginPassword, setLoginPassword] = useState("");
            const [loginError, setLoginError] = useState("");

            const handleLogin = async (e) => {
                e.preventDefault();
                setLoading(true);
                try {
                    const response = await fetch(`${API_BASE}/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username: loginUsername, password: loginPassword })
                    });
                    const data = await response.json();
                    if (response.ok && data.status === "success") {
                        setIsLoggedIn(true);
                        localStorage.setItem("isLoggedIn", "true");
                        setLoginError("");
                    } else {
                        setLoginError(data.detail || "Jina au Password sio sahihi");
                    }
                } catch (err) {
                    setLoginError("Kuna tatizo la mtandao, jaribu tena");
                }
                setLoading(false);
            };

            const handleLogout = () => {
                setIsLoggedIn(false);
                localStorage.removeItem("isLoggedIn");
            };
"""

login_ui = """
            if (!isLoggedIn) {
                return (
                    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
                        <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-6">
                            <div className="flex justify-center mb-6">
                                <div className="bg-blue-600 p-4 rounded-full">
                                    <i className="fas fa-users text-white text-3xl"></i>
                                </div>
                            </div>
                            <h2 className="text-2xl font-bold text-center text-gray-800 mb-6">Ingia Kwenye Mfumo</h2>
                            
                            {loginError && (
                                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                                    {loginError}
                                </div>
                            )}
                            
                            <form onSubmit={handleLogin}>
                                <div className="mb-4">
                                    <label className="block text-gray-700 text-sm font-bold mb-2">Jina la Mtumiaji (Username)</label>
                                    <input 
                                        type="text" 
                                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                        value={loginUsername}
                                        onChange={(e) => setLoginUsername(e.target.value)}
                                        required
                                    />
                                </div>
                                <div className="mb-6">
                                    <label className="block text-gray-700 text-sm font-bold mb-2">Neno la Siri (Password)</label>
                                    <input 
                                        type="password" 
                                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                        value={loginPassword}
                                        onChange={(e) => setLoginPassword(e.target.value)}
                                        required
                                    />
                                </div>
                                <button 
                                    type="submit" 
                                    disabled={loading}
                                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg flex items-center justify-center"
                                >
                                    {loading ? <i className="fas fa-spinner fa-spin"></i> : "Ingia"}
                                </button>
                            </form>
                        </div>
                    </div>
                );
            }

            return (
"""

logout_btn = """
                        <div className="flex justify-between items-center bg-white p-4 rounded-lg shadow mb-4">
                            <h1 className="text-3xl font-bold text-gray-800"><i className="fas fa-users text-blue-600 mr-3"></i>CHF Member Directory</h1>
                            <button onClick={handleLogout} className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg flex items-center gap-2">
                                <i className="fas fa-sign-out-alt"></i> Toka Nje
                            </button>
                        </div>
"""

content = content.replace('function App() {', login_states)
content = content.replace('return (', login_ui, 1) # Only replace the FIRST 'return ('
content = content.replace('<h1 className="text-3xl font-bold text-gray-800"><i className="fas fa-users text-blue-600 mr-3"></i>CHF Member Directory</h1>', logout_btn)

with open(file_path, 'w') as f:
    f.write(content)

print("index.html updated successfully!")
