// 📄 app/tos/page.js
import Link from 'next/link';
import { Home } from 'lucide-react';

export const metadata = {
  title: 'Terms of Service - Clearway Discord Bot',
  description: 'Terms of Service for Clearway Discord Bot',
}

export default function ToSPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Navigation */}
      <nav className="border-b border-gray-800 bg-black/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">C</span>
              </div>
              <span className="text-xl font-semibold">Clearway</span>
            </Link>
            <div className="flex items-center space-x-6">
              <Link href="/" className="text-gray-400 hover:text-white transition-colors flex items-center space-x-1">
                <Home className="w-4 h-4" />
                <span>Home</span>
              </Link>
              <Link href="/privacy-policy" className="text-gray-400 hover:text-white transition-colors">
                Privacy
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-16">
        <div className="mb-12">
          <h1 className="text-4xl font-bold mb-4">Terms of Service</h1>
          <p className="text-gray-400">Last updated: August 25, 2024</p>
        </div>

        <div className="prose prose-invert max-w-none">
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Acceptance of Terms</h2>
            <p className="text-gray-300 mb-4">
              By adding Clearway to your Discord server or using any of its commands, you agree to these Terms of Service. If you don't agree with these terms, please don't use the bot.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Description of Service</h2>
            <p className="text-gray-300 mb-4">
              Clearway is a Discord bot that provides various utility functions including:
            </p>
            <ul className="text-gray-300 space-y-2 mb-4">
              <li>• Web search capabilities via DuckDuckGo</li>
              <li>• YouTube video search through Piped</li>
              <li>• Weather information and forecasts</li>
              <li>• Stock market data and charts</li>
              <li>• Wikipedia article summaries</li>
              <li>• Dictionary definitions</li>
              <li>• Image search functionality</li>
              <li>• Random animal pictures</li>
              <li>• Discord server moderation tools</li>
              <li>• Role management features</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Acceptable Use</h2>
            <p className="text-gray-300 mb-4">
              You agree to use Clearway responsibly and in compliance with Discord's Terms of Service. You may not:
            </p>
            <ul className="text-gray-300 space-y-2 mb-4">
              <li>• Use the bot for illegal activities</li>
              <li>• Attempt to overload or abuse the bot's systems</li>
              <li>• Use the bot to harass, spam, or harm other users</li>
              <li>• Try to exploit vulnerabilities or bypass rate limits</li>
              <li>• Use the bot in a way that violates Discord's Community Guidelines</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Rate Limits and Availability</h2>
            <p className="text-gray-300 mb-4">
              Clearway implements rate limits to ensure fair usage and prevent abuse. Commands are limited to prevent spam and ensure the bot remains responsive for all users. We strive for high uptime but cannot guarantee 100% availability.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Third-Party Content</h2>
            <p className="text-gray-300 mb-4">
              Clearway retrieves content from various third-party services including search engines, weather services, and financial data providers. We are not responsible for the accuracy, completeness, or appropriateness of third-party content. Users should verify important information from primary sources.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Intellectual Property</h2>
            <p className="text-gray-300 mb-4">
              The Clearway bot and its original code are the intellectual property of the bot operator. Third-party content accessed through the bot remains the property of its respective owners. Users are responsible for respecting copyright and other intellectual property rights when using bot features.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Privacy</h2>
            <p className="text-gray-300 mb-4">
              Our approach to privacy is simple: we don't collect your data. Please see our Privacy Policy for detailed information about how we handle (or rather, don't handle) user information.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Disclaimers and Limitations</h2>
            <p className="text-gray-300 mb-4">
              Clearway is provided "as is" without warranties of any kind. We are not liable for:
            </p>
            <ul className="text-gray-300 space-y-2 mb-4">
              <li>• Inaccurate information from third-party sources</li>
              <li>• Service interruptions or downtime</li>
              <li>• Financial decisions made based on stock data</li>
              <li>• Any damages resulting from bot usage</li>
            </ul>
            <p className="text-gray-300 mb-4">
              <strong>Important:</strong> Stock prices and financial information are for informational purposes only and should not be used as the sole basis for investment decisions.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Termination</h2>
            <p className="text-gray-300 mb-4">
              We reserve the right to terminate or suspend access to Clearway for users who violate these terms. You may stop using the bot at any time by removing it from your server.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Governing Law</h2>
            <p className="text-gray-300 mb-4">
              These Terms of Service are governed by the laws of the United States. Any disputes will be resolved in accordance with U.S. federal and applicable state laws.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Changes to Terms</h2>
            <p className="text-gray-300 mb-4">
              We may update these Terms of Service from time to time. Continued use of the bot after changes are posted constitutes acceptance of the new terms. Major changes will be announced through appropriate channels.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">Contact Information</h2>
            <p className="text-gray-300">
              Questions about these Terms of Service? Contact us at: <a href="mailto:support@heysonder.xyz" className="text-blue-400 hover:text-blue-300">support@heysonder.xyz</a>
            </p>
          </section>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-800 bg-gray-900/50 backdrop-blur-xl">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <div className="text-center text-gray-400">
            <p>© 2024 Clearway Discord Bot. Contact: support@heysonder.xyz</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
