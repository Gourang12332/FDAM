'use client';
import { useForm } from 'react-hook-form';
import { useState } from 'react';
import { LogIn } from 'lucide-react';
import { useRouter } from 'next/navigation';
import './(slides)/login/login.css';

export default function Page() {
  const { register, handleSubmit } = useForm();
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const onSubmit = async (data: any) => {
    setLoading(true);

    const formData = new FormData();
    formData.append('username', data.email);
    formData.append('password', data.password);

    const res = await fetch('https://precise-divine-lab.ngrok-free.app/api/v1/auth/login', {
      method: 'POST',
      body: formData,
    });

    console.log(res);
    setLoading(false);
    if (res.ok) {
      alert('Logged in');
      router.push('/dashboard');
    } else {
      alert('Login failed');
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center relative bg-cover bg-center"
      style={{ backgroundImage: "url('/your-background-image.jpg')" }}
    >
      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-purple-900 to-black opacity-70"></div>

      {/* Login Form */}
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="relative z-10 w-full max-w-md bg-white/10 backdrop-blur-md rounded-xl p-8 space-y-6 shadow-2xl animate-fade-in"
      >
        {/* Image Slot */}
        <div className="flex justify-center">
          <img
            src="https://img.freepik.com/free-vector/colorful-bird-illustration-gradient_343694-1741.jpg" // Replace this with your image path
            alt="Your Custom Image"
            className="w-24 h-24 rounded-full border-4 border-white shadow-lg"
          />
        </div>

        <h2 className="text-4xl font-bold text-white text-center">Welcome Back</h2>
        <p className="text-center text-white/80">Login to your account</p>

        <div className="space-y-4">
          <input
            {...register('email')}
            type="email"
            placeholder="Email"
            className="w-full p-3 bg-white/20 text-white border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 placeholder-white/70"
            required
          />
          <input
            {...register('password')}
            type="password"
            placeholder="Password"
            className="w-full p-3 bg-white/20 text-white border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 placeholder-white/70"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full p-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-lg flex items-center justify-center gap-2 transition duration-200"
        >
          <LogIn className="w-5 h-5" />
          {loading ? 'Logging in...' : 'Login'}
        </button>

        <p className="text-center text-sm text-white/80">
          New user?{' '}
          <a href="/SignIn" className="text-blue-400 hover:underline">
            Sign up
          </a>
        </p>
      </form>
    </div>
  );
}