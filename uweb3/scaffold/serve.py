"""Starts a simple application development server."""

# Application
import base

def main():
  app = base.main()
  app.serve(hot_reloading=True)


if __name__ == '__main__':
  main()
