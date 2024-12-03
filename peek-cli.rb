class PeekCli < Formula
  desc "CLI for interacting with the Peek API"
  homepage "https://github.com/peek-travel/peek-cli"
  url "https://github.com/peek-travel/peek-cli/archive/refs/tags/v0.1.tar.gz"
  sha256 "CHECKSUM_OF_TARBALL"
  license "MIT"

  depends_on "python@3.9"

  def install
    virtualenv_install_with_resources
  end
end