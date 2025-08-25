// 📄 app/page.js (Homepage)
import Link from 'next/link';
import { FileText, Shield, ArrowRight, ExternalLink } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Navigation */}
      <nav className="border-b border-gray-800 bg-black/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">C</span>
              </div>
              <span className="text-xl font-semibold">Clearway</span>
            </div>
            <div className="flex items-center space-x-6">
              <Link href="/privacy-policy" className="text-gray-400 hover:text-white transition-colors">
                Privacy
              </Link>
              <Link href="/tos" className="text-gray-400 hover:text-white transition-colors">
                Terms
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-blue-900/20 to-black"></div>
        <div className="relative max-w-6xl mx-auto px-6 py-24">
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-500 rounded-2xl flex items-center justify-center mx-auto mb-8">
              <span className="text-white font-bold text-2xl">C</span>
            </div>
            <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
              Clearway Discord Bot
            </h1>
            <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto">
              A powerful Discord bot offering search, weather, stock prices, media tools, and more - all with a focus on privacy and simplicity.
            </p>
            
            {/* Feature Grid */}
            <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-16">
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 backdrop-blur-sm">
                <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center mb-4">
                  <ExternalLink className="w-5 h-5 text-blue-400" />
                </div>
                <h3 className="font-semibold mb-2">Web Search & Media</h3>
                <p className="text-sm text-gray-400">DuckDuckGo search, YouTube via Piped, Wikipedia, image search, and more</p>
              </div>
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 backdrop-blur-sm">
                <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center mb-4">
                  <Shield className="w-5 h-5 text-purple-400" />
                </div>
                <h3 className="font-semibold mb-2">Privacy First</h3>
                <p className="text-sm text-gray-400">No data collection, no analytics, no tracking - just helpful features</p>
              </div>
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 backdrop-blur-sm">
                <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center mb-4">
                  <FileText className="w-5 h-5 text-green-400" />
                </div>
                <h3 className="font-semibold mb-2">Utility Commands</h3>
                <p className="text-sm text-gray-400">Weather, stocks, definitions, moderation tools, and role management</p>
              </div>
            </div>

            {/* Legal Links */}
            <div className="flex justify-center space-x-6">
              <Link
                href="/privacy-policy"
                className="flex items-center space-x-2 bg-gray-900 hover:bg-gray-800 border border-gray-700 rounded-lg px-6 py-3 transition-colors"
              >
                <Shield className="w-4 h-4" />
                <span>Privacy Policy</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/tos"
                className="flex items-center space-x-2 bg-gray-900 hover:bg-gray-800 border border-gray-700 rounded-lg px-6 py-3 transition-colors"
              >
                <FileText className="w-4 h-4" />
                <span>Terms of Service</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-800 bg-gray-900/50 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="text-center text-gray-400">
            <p>© 2024 Clearway Discord Bot. Contact: support@heysonder.xyz</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
