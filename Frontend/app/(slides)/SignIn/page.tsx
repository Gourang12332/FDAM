'use client';
import { useForm } from 'react-hook-form';
import { useState } from 'react';
import { UserPlus } from 'lucide-react';
import './SignIn.css'

export default function Page() {
  const { register, handleSubmit } = useForm();
  const [loading, setLoading] = useState(false);

  const onSubmit = async (data: any) => {
    setLoading(true);

    const jsonData = {
      email: data.email,
      full_name: data.name,
      is_recruiter: false, // Change to true if needed
      password: data.password,
    };

    const res = await fetch('https://precise-divine-lab.ngrok-free.app/api/v1/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(jsonData),
    });

    setLoading(false);
    if (res.ok) {
      alert('Signed up');
    } else {
      alert('Signup failed');
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center relative bg-cover bg-center"
      style={{ backgroundImage: "url('/your-background-image.jpg')" }}
    >
      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-purple-900 to-black opacity-70"></div>

      {/* Registration Form */}
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="relative z-10 w-full max-w-md bg-white/10 backdrop-blur-md rounded-xl p-8 space-y-6 shadow-2xl animate-fade-in"
      >
        <div className="flex justify-center">
          <img
            src="https://img.freepik.com/free-vector/colorful-bird-illustration-gradient_343694-1741.jpg" // Replace this with your image path
            alt="Your Custom Image"
            className="w-24 h-24 rounded-full border-4 border-white shadow-lg"
          />
        </div>

        <h2 className="text-4xl font-bold text-white text-center">Create Account</h2>
        <p className="text-center text-white/80">Join Resume Checker today</p>

        <div className="space-y-4">
          <input
            {...register('name')}
            type="text"
            placeholder="Full Name"
            className="w-full p-3 bg-white/20 text-white border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-400 placeholder-white/70"
            required
          />
          <input
            {...register('email')}
            type="email"
            placeholder="Email"
            className="w-full p-3 bg-white/20 text-white border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-400 placeholder-white/70"
            required
          />
          <input
            {...register('password')}
            type="password"
            placeholder="Password"
            className="w-full p-3 bg-white/20 text-white border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-400 placeholder-white/70"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full p-3 bg-gradient-to-r from-green-500 to-teal-600 hover:from-green-600 hover:to-teal-700 text-white rounded-lg flex items-center justify-center gap-2 transition duration-200"
        >
          <UserPlus className="w-5 h-5" />
          {loading ? 'Signing up...' : 'Sign Up'}
        </button>

        <p className="text-center text-sm text-white/80">
          Already have an account?{' '}
          <a href="/login" className="text-green-400 hover:underline">
            Login
          </a>
        </p>
      </form>
    </div>
  );
}