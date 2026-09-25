{-# LANGUAGE OverloadedStrings #-}

module Isoprax.Kernel.Identity
  ( canonicalIdentity
  , canonicalJson
  ) where

import qualified Crypto.Hash.SHA256 as SHA256
import Data.Aeson (Value (..))
import qualified Data.Aeson.KeyMap
import Data.Aeson.RFC8785 (encodeCanonical)
import qualified Data.ByteString as ByteString
import qualified Data.ByteString.Lazy as LazyByteString
import Data.Scientific (base10Exponent, coefficient, toRealFloat)
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as TextEncoding
import Data.Word (Word8)
import Isoprax.Kernel.Types

canonicalIdentity :: Value -> Either KernelError CanonicalIdentity
canonicalIdentity value = do
  validateIJson value
  let bytes = LazyByteString.toStrict (encodeCanonical value)
      digest = SHA256.hash bytes
      canonical = TextEncoding.decodeUtf8 bytes
      hexadecimal = Text.pack (concatMap byteHex (ByteString.unpack digest))
  pure (CanonicalIdentity canonical hexadecimal)

canonicalJson :: Value -> Either KernelError Text
canonicalJson value = identityCanonical <$> canonicalIdentity value

validateIJson :: Value -> Either KernelError ()
validateIJson value = case value of
  Object members -> traverse_ validateIJson (map snd (Data.Aeson.KeyMap.toList members))
  Array values -> traverse_ validateIJson (foldr (:) [] values)
  Number number ->
    let asDouble = toRealFloat number :: Double
        integerToken = base10Exponent number == 0
        integerValue = coefficient number
    in if isNaN asDouble || isInfinite asDouble
        then invalid "number is outside the finite IEEE-754 domain"
        else if integerToken && abs integerValue > 9007199254740991
          then invalid "integer is outside the interoperable safe-integer range"
          else Right ()
  String _ -> Right ()
  Bool _ -> Right ()
  Null -> Right ()
  where
    invalid message = Left (KernelError InvalidIdentityValue message)

traverse_ :: (a -> Either e b) -> [a] -> Either e ()
traverse_ _ [] = Right ()
traverse_ action (value : rest) = action value >> traverse_ action rest

byteHex :: Word8 -> String
byteHex byte =
  let digits = "0123456789abcdef"
      value = fromIntegral byte :: Int
  in [digits !! (quot value 16), digits !! (rem value 16)]
