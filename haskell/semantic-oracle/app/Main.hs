{-# LANGUAGE OverloadedStrings #-}

module Main (main) where

import Data.Aeson (Value, eitherDecode, encode)
import Data.ByteString.Lazy qualified as LazyByteString
import Data.Text qualified as Text
import Isoprax.Oracle (runFixture)
import System.Exit (exitFailure)

main :: IO ()
main = do
  input <- LazyByteString.getContents
  case eitherDecode input :: Either String Value of
    Left message -> failWith message
    Right fixture -> case runFixture fixture of
      Left message -> failWith (Text.unpack message)
      Right output -> LazyByteString.putStrLn (encode output)
  where
    failWith message = do
      putStrLn message
      exitFailure
